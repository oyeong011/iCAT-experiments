#!/usr/bin/env python3
"""m1-20261126: add region timers to a copy of conv_ftl.c (SmartGC tree or iCAT revC tree). GC behaviour is unchanged:
each timed function is renamed <name>__m1raw and a wrapper with the original name calls it between two clock reads.
  kernel build : clock = ktime_get_ns()                -> ELAPSED time (kernel ktime), NOT CPU time
  userspace sim: clock = CLOCK_THREAD_CPUTIME_ID (-DM1PROF_CPU) -> thread CPU time
Counters are per partition, reset at measurement "start", printed (M1PROF lines) at "stop" and at module removal.
Usage: m1prof_patch.py <conv_ftl.c> smartgc|icat   (edits the file in place; refuses a file already patched)"""
import re, sys

path, tree = sys.argv[1], sys.argv[2]
s = open(path).read()
assert 'M1PROF' not in s, 'already patched'

REG = ['GC', 'SELECT', 'LEARN', 'REWARD', 'BUF_ABSORB', 'BUF_UNBUF', 'BUF_DRAIN']
HDR = r'''
/* ---- m1-20261126 region timers (see result/m1-20261126/tools/m1prof_patch.py) ---- */
#ifdef M1PROF_CPU
#include <time.h>
static inline uint64_t m1p_now(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
	return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}
#define M1P_CLOCK "thread_cputime"
#else
#define m1p_now() ktime_get_ns()
#define M1P_CLOCK "ktime_elapsed"
#endif
enum { M1P_GC, M1P_SELECT, M1P_LEARN, M1P_REWARD, M1P_BUF_ABSORB, M1P_BUF_UNBUF, M1P_BUF_DRAIN, M1P_N };
static const char *const m1p_name[M1P_N] = { %NAMES% };
struct m1p_ctr { uint64_t calls, ns, max_ns; };
static struct m1p_ctr m1p[4][M1P_N];
#define M1P_PART(ftl) ((ftl)->tuner.part_id & 3)
static inline void m1p_add(uint32_t part, int id, uint64_t t0)
{
	uint64_t d = m1p_now() - t0;
	struct m1p_ctr *c = &m1p[part][id];

	c->calls++;
	c->ns += d;
	if (d > c->max_ns)
		c->max_ns = d;
}
static void m1p_reset(void)
{
	memset(m1p, 0, sizeof(m1p));
}
static void m1p_print(const char *when)
{
	uint32_t p;
	int i;

	for (p = 0; p < 4; p++)
		for (i = 0; i < M1P_N; i++)
			if (m1p[p][i].calls)
				NVMEV_INFO("M1PROF when=%s clock=%s part=%u region=%s calls=%llu ns=%llu max_ns=%llu\n",
					   when, M1P_CLOCK, p, m1p_name[i], m1p[p][i].calls, m1p[p][i].ns,
					   m1p[p][i].max_ns);
}
/* ---- end m1 region timers ---- */
'''.replace('%NAMES%', ', '.join(f'"{r}"' for r in REG))


def once(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= 1, f'anchor not found: {old[:70]!r}'
    s = s.replace(old, new, count)


def rename_def(sig_prefix, raw_name, name):
    """Rename the FIRST definition whose text starts with sig_prefix (name -> raw_name)."""
    i = s.find(sig_prefix)
    assert i >= 0, sig_prefix
    j = i + len(sig_prefix)
    return s[:i] + sig_prefix.replace(name + '(', raw_name + '(') + s[j:]


once('static bool measurement_manual;\n', 'static bool measurement_manual;\n' + HDR)
# reset at start, print at stop
once('\t\tconv_measure_host_bytes = 0;\n\t\tconv_measure_epoch++;\n',
     '\t\tconv_measure_host_bytes = 0;\n\t\tm1p_reset();\n\t\tconv_measure_epoch++;\n')
once('\t\tconv_measure_active = false;\n', '\t\tconv_measure_active = false;\n\t\tm1p_print("stop");\n')
# print at removal (before the per-partition loop of conv_remove_namespace)
m = re.search(r'void conv_remove_namespace\(struct nvmev_ns \*ns\)\n\{\n(.*?\n)\n', s, re.S)
assert m
s = s[:m.end()] + '\tm1p_print("remove");\n' + s[m.end():]

W = {}
# common: whole GC and victim selection (selection includes SmartGC step = Q update + state scoring; iCAT = CAT score scan)
s = rename_def('static int do_gc(struct conv_ftl *conv_ftl, bool force)\n{', 'do_gc__m1raw', 'do_gc')
s = rename_def('static struct line *select_victim_line(struct conv_ftl *conv_ftl, bool force)\n{',
               'select_victim_line__m1raw', 'select_victim_line')
WRAP_SELECT = '''static struct line *select_victim_line(struct conv_ftl *conv_ftl, bool force)
{
	uint64_t t0 = m1p_now();
	struct line *l = select_victim_line__m1raw(conv_ftl, force);

	m1p_add(M1P_PART(conv_ftl), M1P_SELECT, t0);
	return l;
}

'''
WRAP_GC = '''static int do_gc(struct conv_ftl *conv_ftl, bool force)
{
	uint64_t t0 = m1p_now();
	int r = do_gc__m1raw(conv_ftl, force);

	m1p_add(M1P_PART(conv_ftl), M1P_GC, t0);
	return r;
}

'''
once('static int do_gc__m1raw(', WRAP_SELECT + 'static int do_gc__m1raw(')
# do_gc wrapper right after do_gc__m1raw: insert before the first function that follows it
i = s.find('static int do_gc__m1raw(')
k = s.find('\nstatic void foreground_gc(struct conv_ftl *conv_ftl)\n{', i)
assert k > i
s = s[:k + 1] + WRAP_GC + s[k + 1:]

if tree == 'icat':
    s = rename_def('static void watgc_v2_on_gc(struct conv_ftl *ftl, uint64_t now_ns)\n{', 'watgc_v2_on_gc__m1raw', 'watgc_v2_on_gc')
    i = s.find('static void watgc_v2_on_gc__m1raw(')
    k = s.find('\nstatic void watgc_v2_report(struct conv_ftl *ftl)\n{', i)
    assert k > i
    s = s[:k + 1] + '''static void watgc_v2_on_gc(struct conv_ftl *ftl, uint64_t now_ns)
{
	uint64_t t0 = m1p_now();

	watgc_v2_on_gc__m1raw(ftl, now_ns);
	m1p_add(M1P_PART(ftl), M1P_LEARN, t0);
}

''' + s[k + 1:]
elif tree == 'smartgc':
    s = rename_def('static bool smartgc_step(struct conv_ftl *ftl, bool thaw)\n{', 'smartgc_step__m1raw', 'smartgc_step')
    once('static struct line *smartgc_select(struct conv_ftl *ftl)\n{', '''static bool smartgc_step(struct conv_ftl *ftl, bool thaw)
{
	uint64_t t0 = m1p_now();
	bool r = smartgc_step__m1raw(ftl, thaw);

	m1p_add(M1P_PART(ftl), M1P_LEARN, t0);
	return r;
}

static struct line *smartgc_select(struct conv_ftl *ftl)
{''')
    s = rename_def('static void smartgc_on_erase(struct conv_ftl *ftl, struct line *line)\n{', 'smartgc_on_erase__m1raw', 'smartgc_on_erase')
    s = rename_def('static bool smartgc_unbuffer(struct conv_ftl *ftl, uint64_t lpn, struct ppa *ppa)\n{', 'smartgc_unbuffer__m1raw', 'smartgc_unbuffer')
    s = rename_def('static bool smartgc_absorb(struct conv_ftl *ftl, uint64_t lpn, struct ppa *ppa)\n{', 'smartgc_absorb__m1raw', 'smartgc_absorb')
    s = rename_def('static void smartgc_drain(struct conv_ftl *ftl, uint32_t sqid, struct buffer *wbuf,\n\t\t\t  struct nand_cmd *swr)\n{',
                   'smartgc_drain__m1raw', 'smartgc_drain')
    # drain calls unbuffer before its wrapper exists: forward-declare the wrapper
    once('static bool smartgc_unbuffer__m1raw(', 'static bool smartgc_unbuffer(struct conv_ftl *ftl, uint64_t lpn, struct ppa *ppa);\n'
         'static bool smartgc_unbuffer__m1raw(')
    once('static void smartgc_reset_learning(struct conv_ftl *ftl)\n{', '''static void smartgc_on_erase(struct conv_ftl *ftl, struct line *line)
{
	uint64_t t0 = m1p_now();

	smartgc_on_erase__m1raw(ftl, line);
	m1p_add(M1P_PART(ftl), M1P_REWARD, t0);
}

static bool smartgc_unbuffer(struct conv_ftl *ftl, uint64_t lpn, struct ppa *ppa)
{
	uint64_t t0 = m1p_now();
	bool r = smartgc_unbuffer__m1raw(ftl, lpn, ppa);

	m1p_add(M1P_PART(ftl), M1P_BUF_UNBUF, t0);
	return r;
}

static bool smartgc_absorb(struct conv_ftl *ftl, uint64_t lpn, struct ppa *ppa)
{
	uint64_t t0 = m1p_now();
	bool r = smartgc_absorb__m1raw(ftl, lpn, ppa);

	m1p_add(M1P_PART(ftl), M1P_BUF_ABSORB, t0);
	return r;
}

static void smartgc_drain(struct conv_ftl *ftl, uint32_t sqid, struct buffer *wbuf,
			  struct nand_cmd *swr)
{
	uint64_t t0 = m1p_now();

	smartgc_drain__m1raw(ftl, sqid, wbuf, swr);
	m1p_add(M1P_PART(ftl), M1P_BUF_DRAIN, t0);
}

static void smartgc_reset_learning(struct conv_ftl *ftl)
{''')
else:
    sys.exit('tree must be smartgc or icat')
open(path, 'w').write(s)
print('patched', path, tree)
