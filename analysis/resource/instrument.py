"""Copy an online-*-src tree and add resource counters under #ifdef RES_INSTR (resource-20261114).
Without RES_INSTR the build must match the original .text; CONV_FIXED_ARM only affects the learner-off (#else) init.
usage: instrument.py <src_dir> <dst_dir>"""
import re, shutil, sys
src, dst = sys.argv[1:3]
shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.o', '*.ko', '*.mod', '*.mod.c', '.*.cmd', 'modules.order', 'Module.symvers'))
p = f'{dst}/conv_ftl.c'; s = open(p).read()
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (old, s.count(old)); s = s.replace(old, new)
# slots: 0 do_gc (includes on_gc), 1 on_gc, 2 observe, 3 reward update, 4 selection, 5 sample printk, 6 set_arm
sub('static void watgc_v2_init(struct conv_ftl *ftl, uint32_t ns_id, uint32_t part_id);\n',
'''static void watgc_v2_init(struct conv_ftl *ftl, uint32_t ns_id, uint32_t part_id);
#ifdef RES_INSTR
#define RES_SLOTS 7
static uint64_t res_n[SSD_PARTITIONS][RES_SLOTS], res_sum[SSD_PARTITIONS][RES_SLOTS], res_max[SSD_PARTITIONS][RES_SLOTS];
static uint64_t res_mark[SSD_PARTITIONS];
static inline void res_add(uint32_t part, int slot, uint64_t d)
{
	res_n[part][slot]++; res_sum[part][slot] += d;
	if (d > res_max[part][slot]) res_max[part][slot] = d;
}
#define RES_NOW() ktime_get_ns()
#define RES_DECL(v) uint64_t v = ktime_get_ns()
#else
#define RES_DECL(v)
#endif
''')
# observe: reward update = entry .. just before the selection branch
sub('\tbool had_coverage, first_coverage;\n\n\tt->windows++;', '\tbool had_coverage, first_coverage;\n\tRES_DECL(res_t0);\n\n\tt->windows++;')
sub('\tif (!t->settled)\n\t\treturn watgc_v2_choose_search(t);',
    '#ifdef RES_INSTR\n\tres_mark[t->part_id] = RES_NOW();\n\tres_add(t->part_id, 3, res_mark[t->part_id] - res_t0);\n#endif\n\tif (!t->settled)\n\t\treturn watgc_v2_choose_search(t);')
# observe call site: total + selection (mark .. return)
sub('\tnext = watgc_v2_observe(ftl, host, gc_pages, sample);\n',
'''#ifdef RES_INSTR
	{ uint64_t r0 = RES_NOW(), r1;
	next = watgc_v2_observe(ftl, host, gc_pages, sample);
	r1 = RES_NOW(); res_add(t->part_id, 2, r1 - r0); res_add(t->part_id, 4, r1 - res_mark[t->part_id]); }
	{ uint64_t r0 = RES_NOW();
#else
	next = watgc_v2_observe(ftl, host, gc_pages, sample);
#endif
''')
m = re.search(r'\tNVMEV_INFO\("WATGC_V2 sample .*?\);\n', s, re.S); assert m
s = s[:m.end()] + '#ifdef RES_INSTR\n\tres_add(t->part_id, 5, RES_NOW() - r0); }\n#endif\n' + s[m.end():]
sub('\t\twatgc_v2_set_arm(ftl, next);\n',
    '\t\t{ RES_DECL(r0);\n\t\twatgc_v2_set_arm(ftl, next);\n#ifdef RES_INSTR\n\t\tres_add(t->part_id, 6, RES_NOW() - r0);\n#endif\n\t\t}\n')
sub('''	if (!measurement_manual || conv_measure_active)
		watgc_v2_on_gc(conv_ftl, ktime_get_ns());''', '''	if (!measurement_manual || conv_measure_active) {
#ifdef RES_INSTR
		uint64_t r0 = RES_NOW();
		watgc_v2_on_gc(conv_ftl, r0);
		res_add(conv_ftl->tuner.part_id, 1, RES_NOW() - r0);
#else
		watgc_v2_on_gc(conv_ftl, ktime_get_ns());
#endif
	}''')
sub('\t\tdo_gc(conv_ftl, true);\n', '''#ifdef RES_INSTR
		{ uint64_t r0 = RES_NOW(); bool on = !measurement_manual || conv_measure_active;
		do_gc(conv_ftl, true);
		if (on) res_add(conv_ftl->tuner.part_id, 0, RES_NOW() - r0); }
#else
		do_gc(conv_ftl, true);
#endif
''')
sub('''	ftl->tuner.best_arm = WATGC_V2_INITIAL_ARM;
	watgc_v2_set_arm(ftl, WATGC_V2_INITIAL_ARM);
}''', '''#ifdef CONV_FIXED_ARM
	ftl->tuner.best_arm = CONV_FIXED_ARM;
	watgc_v2_set_arm(ftl, CONV_FIXED_ARM);
#else
	ftl->tuner.best_arm = WATGC_V2_INITIAL_ARM;
	watgc_v2_set_arm(ftl, WATGC_V2_INITIAL_ARM);
#endif
}''')
sub('\t\twatgc_v2_report(&conv_ftls[i]);\n', '''		watgc_v2_report(&conv_ftls[i]);
#ifdef RES_INSTR
		{ int j; static const char *nm[RES_SLOTS] = { "dogc", "ongc", "observe", "update", "select", "log", "setarm" };
		for (j = 0; j < RES_SLOTS; j++)
			NVMEV_INFO("RESOURCE part=%u slot=%s n=%llu sum_ns=%llu max_ns=%llu\\n", i, nm[j], res_n[i][j], res_sum[i][j], res_max[i][j]);
		NVMEV_INFO("RESOURCE part=%u arm=%u sizeof_tuner=%zu sizeof_arm=%zu arm_slots=%zu sizeof_param=%zu sizeof_conv_ftl=%zu sizeof_line=%zu tt_lines=%u\\n",
			   i, conv_ftls[i].tuner.current_arm, sizeof(struct watgc_v2_tuner), sizeof(struct watgc_v2_arm),
			   ARRAY_SIZE(conv_ftls[i].tuner.arm), sizeof(struct watgc_v2_param), sizeof(struct conv_ftl),
			   sizeof(struct line), conv_ftls[i].lm.tt_lines); }
#endif
''')
open(p, 'w').write(s); print('ok', dst)
