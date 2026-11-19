// SPDX-License-Identifier: GPL-2.0-only
/*
 * Userspace driver for the unmodified conventional FTL (conv_ftl.c, ssd.c,
 * pqueue.c).  It sends NVMe write/read commands straight to
 * conv_proc_nvme_io_cmd(), checks the FTL and SmartGC invariants while it
 * runs, and prints WAF and wear.  It is a logic check, not a measurement:
 * time is a fake clock, the channel bandwidth model is replaced by a
 * zero-delay stub and no data is stored.  Build and run with run.sh.
 */
#include "kshim.h"

bool kshim_verbose;
uint64_t kshim_now_ns = 1;
struct nvmev_dev kshim_vdev;
struct nvmev_dev *nvmev_vdev = &kshim_vdev;

/* Found through -I: run.sh can point SIM_SRC at another copy of the module source. */
#include "pqueue/pqueue.c"
#include "ssd.c"
#include "conv_ftl.c"

/* Sources older than smartgc-src have no wear or SmartGC bookkeeping to check. */
#ifdef SMARTGC_STATES
#define HAVE_SMARTGC 1
#define IS_SMARTGC (CONV_GC_POLICY == 3)
#else
#define HAVE_SMARTGC 0
#define IS_SMARTGC 0
#endif

/*
 * The real channel model keeps a credit window anchored at the CPU clock; the
 * fake clock here does not follow NAND busy time, so transfers take no time.
 */
void chmodel_init(struct channel_model *ch, uint64_t bandwidth)
{
}

uint64_t chmodel_request(struct channel_model *ch, uint64_t request_time, uint64_t length)
{
	return request_time;
}

void schedule_internal_operation(int sqid, unsigned long long nsecs_target,
				 struct buffer *write_buffer, size_t buffs_to_release)
{
	buffer_release(write_buffer, buffs_to_release);
}

static uint64_t sim_rng = 0x1234567887654321ULL;

static uint64_t sim_rand(void)
{
	sim_rng ^= sim_rng >> 12;
	sim_rng ^= sim_rng << 25;
	sim_rng ^= sim_rng >> 27;
	return sim_rng * 0x2545F4914F6CDD1DULL;
}

#define CHECK(cond)                                                              \
	do {                                                                     \
		if (!(cond)) {                                                   \
			fprintf(stderr, "INVARIANT FAILED %s:%d: %s\n", __FILE__, \
				__LINE__, #cond);                                \
			exit(1);                                                 \
		}                                                                \
	} while (0)

/* Recount everything the FTL and SmartGC track incrementally. */
static void check_invariants(struct nvmev_ns *ns)
{
	struct conv_ftl *ftls = ns->ftls;
	uint32_t part, i;
	uint64_t lpn;

	for (part = 0; part < ns->nr_parts; part++) {
		struct conv_ftl *ftl = &ftls[part];
		struct ssdparams *spp = &ftl->ssd->sp;
		struct line_mgmt *lm = &ftl->lm;
		uint64_t valid = 0, mapped = 0, buffered = 0, line_buffered = 0;
		uint32_t frozen = 0, victim = 0, draining = 0, erased = 0;
#if HAVE_SMARTGC
		struct smartgc *sg = &ftl->smartgc;
#endif

		for (i = 0; i < lm->tt_lines; i++) {
			struct line *line = &lm->lines[i];

			CHECK(line->vpc >= 0 && line->ipc >= 0);
			CHECK(line->vpc + line->ipc <= spp->pgs_per_line);
			valid += line->vpc;
			victim += line->pos != 0;
#if HAVE_SMARTGC
			CHECK((uint32_t)line->vpc >= line->buf_cnt);
			CHECK(!line->frozen || line->closed);
			CHECK(!line->pos || line->closed);
			line_buffered += line->buf_cnt;
			frozen += line->frozen;
			draining += line->draining;
			erased += line->erase_cnt;
#endif
		}
		for (lpn = 0; lpn < spp->tt_pgs; lpn++) {
			struct ppa ppa = ftl->maptbl[lpn];

#if HAVE_SMARTGC
			if (sg->buffered && test_bit(lpn, sg->buffered)) {
				CHECK(ppa.ppa != UNMAPPED_PPA);
				buffered++;
			}
#endif
			if (ppa.ppa == UNMAPPED_PPA)
				continue;
			mapped++;
			CHECK(get_pg(ftl->ssd, &ppa)->status == PG_VALID);
			CHECK(get_rmap_ent(ftl, &ppa) == lpn);
		}
		CHECK(valid == mapped);
		CHECK(victim == lm->victim_line_cnt);
		CHECK(lm->free_line_cnt >= 1);
#if HAVE_SMARTGC
		CHECK(erased == ftl->stats.total_gc_count);
		CHECK(buffered == sg->buf_pages && line_buffered == sg->buf_pages);
		CHECK(sg->buf_pages <= sg->buf_capacity);
		CHECK(frozen == sg->frozen_cnt && frozen <= sg->frozen_max);
		CHECK(draining == sg->drain_cnt);
#endif
	}
}

static bool submit(struct nvmev_ns *ns, uint8_t opcode, uint64_t lpn, uint32_t pages)
{
	struct nvme_command cmd = { 0 };
	struct nvmev_request req = { .cmd = &cmd, .sq_id = 1, .nsecs_start = kshim_now_ns };
	struct nvmev_result ret = { 0 };

	cmd.rw.opcode = opcode;
	cmd.rw.slba = lpn * (4096 / LBA_SIZE);
	cmd.rw.length = pages * (4096 / LBA_SIZE) - 1;
	return ns->proc_io_cmd(ns, &req, &ret);
}

static void measurement(struct nvmev_ns *ns, const char *command)
{
	struct file file = { .data = ns };
	loff_t offset = 0;

	CHECK(conv_measure_write(&file, command, strlen(command), &offset) ==
	      (ssize_t)strlen(command));
}

int main(int argc, char **argv)
{
	uint64_t capacity_mib = 8192, overwrite_x = 6, check_every, logical_pages, total, n;
	const char *workload = "zones";
	struct nvmev_ns ns = { 0 };
	struct conv_ftl *ftls;
	char report[4096];
	struct file file = { .data = &ns };
	loff_t offset = 0;
	ssize_t len;
	uint32_t part;
	int i;

	for (i = 1; i < argc; i++) {
		char *value = strchr(argv[i], '=');

		if (!value) {
			fprintf(stderr, "usage: sim [capacity_mib=N] [overwrite_x=N] [workload=zones|uniform] "
					"[verbose=1] [sim_seed=N]"
#if IS_SMARTGC
					" [alpha|gamma|eps_start|eps_min|w|gcbuf=permille] "
					"[eps_halflife=N] [batch=N] [q_init=N] [seed=N] [eq8=0|1]"
#endif
					"\n");
			return 2;
		}
		*value++ = '\0';
		n = strtoull(value, NULL, 0);
		if (!strcmp(argv[i], "capacity_mib")) capacity_mib = n;
		else if (!strcmp(argv[i], "overwrite_x")) overwrite_x = n;
		else if (!strcmp(argv[i], "workload")) workload = value;
		else if (!strcmp(argv[i], "verbose")) kshim_verbose = n;
		else if (!strcmp(argv[i], "sim_seed")) sim_rng += n * 0x9E3779B97F4A7C15ULL;
#if IS_SMARTGC
		else if (!strcmp(argv[i], "alpha")) smartgc_alpha_permille = n;
		else if (!strcmp(argv[i], "gamma")) smartgc_gamma_permille = n;
		else if (!strcmp(argv[i], "eps_start")) smartgc_eps_start_permille = n;
		else if (!strcmp(argv[i], "eps_min")) smartgc_eps_min_permille = n;
		else if (!strcmp(argv[i], "eps_halflife")) smartgc_eps_halflife = n;
		else if (!strcmp(argv[i], "w")) smartgc_w_permille = n;
		else if (!strcmp(argv[i], "batch")) smartgc_batch = n;
		else if (!strcmp(argv[i], "gcbuf")) smartgc_gcbuf_permille = n;
		else if (!strcmp(argv[i], "q_init")) smartgc_q_init = n;
		else if (!strcmp(argv[i], "seed")) smartgc_seed = n;
		else if (!strcmp(argv[i], "eq8")) smartgc_eq8 = n;
#endif
		else {
			fprintf(stderr, "unknown option %s\n", argv[i]);
			return 2;
		}
	}

	measurement_manual = true;
	conv_init_namespace(&ns, 0, capacity_mib << 20, NULL, 0);
	conv_measure_init(&ns);
	ftls = ns.ftls;
	logical_pages = ns.size / 4096;
	total = logical_pages * overwrite_x;
	check_every = max(total / 16, (uint64_t)1);

	/* Precondition: write every logical page once, in order, 32 pages per command. */
	for (n = 0; n + 32 <= logical_pages; n += 32) {
		CHECK(submit(&ns, nvme_cmd_write, n, 32));
		kshim_now_ns += 25000;
	}
	check_invariants(&ns);

	measurement(&ns, "start");
	for (n = 0; n < total; n++) {
		uint64_t lpn, r = sim_rand();

		if (!strcmp(workload, "uniform")) {
			lpn = r % logical_pages;
		} else {
			/* 60 / 30 / 10 % of the writes to 10 / 30 / 60 % of the space */
			uint64_t pick = (r >> 32) % 10, hot = logical_pages / 10, warm = 3 * hot;

			if (pick < 6)
				lpn = r % hot;
			else if (pick < 9)
				lpn = hot + r % warm;
			else
				lpn = hot + warm + r % (logical_pages - hot - warm);
		}
		CHECK(submit(&ns, nvme_cmd_write, lpn, 1));
		if ((n & 15) == 0)
			CHECK(submit(&ns, nvme_cmd_read, sim_rand() % logical_pages, 1));
		kshim_now_ns += 25000; /* 40k IOPS */
		if ((n + 1) % check_every == 0)
			check_invariants(&ns);
	}
	measurement(&ns, "stop");
	check_invariants(&ns);

	len = conv_measure_read(&file, report, sizeof(report) - 1, &offset);
	report[len] = '\0';
	fputs(report, stdout);
	{
		uint64_t host = 0, gc = 0, absorbed = 0, evicted = 0;

		for (part = 0; part < ns.nr_parts; part++) {
			host += ftls[part].stats.host_page_writes;
			gc += ftls[part].stats.gc_page_writes;
#if HAVE_SMARTGC
			absorbed += ftls[part].smartgc.stats.absorbed;
			evicted += ftls[part].smartgc.stats.evicted;
#endif
		}
		CHECK(host == total);
		/* waf: the run scripts' formula.  waf_nand: every NAND program / host page. */
		printf("sim policy=%s workload=%s capacity_mib=%llu host_pages=%llu gc_pages=%llu waf=%.6f waf_nand=%.6f "
		       "invariants=ok\n",
		       conv_gc_policy_name(), workload, (unsigned long long)capacity_mib,
		       (unsigned long long)host, (unsigned long long)gc, 1.0 + (double)gc / host,
		       (double)(host - absorbed + evicted + gc) / host);
	}
	kshim_verbose = true;
	conv_remove_namespace(&ns);
	return 0;
}
