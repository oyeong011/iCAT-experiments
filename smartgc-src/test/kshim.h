// SPDX-License-Identifier: GPL-2.0-only
/*
 * Userspace stand-ins for the kernel interfaces used by conv_ftl.c, ssd.c,
 * channel_model.c and pqueue.c, so that the unmodified FTL can be driven by
 * test/sim.c.  run.sh points every <linux/...> include at this file.
 */
#ifndef KSHIM_H
#define KSHIM_H

#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

typedef uint8_t u8, __u8;
typedef uint16_t u16, __u16, __le16;
typedef uint32_t u32, __u32, __le32;
typedef uint64_t u64, __u64, __le64;
typedef int64_t s64;

#ifndef static_assert
#define static_assert _Static_assert
#endif
#define __user
#define __iomem
#define __maybe_unused __attribute__((unused))
#define __packed __attribute__((packed))
#define le16_to_cpu(x) (x)
#define NSEC_PER_SEC 1000000000L
#define GFP_KERNEL 0
#define KERN_INFO ""
#define KERN_ERR ""

extern bool kshim_verbose;
extern uint64_t kshim_now_ns;

static inline int printk(const char *fmt, ...)
{
	va_list ap;

	if (!kshim_verbose)
		return 0;
	va_start(ap, fmt);
	vfprintf(stdout, fmt, ap);
	va_end(ap);
	return 0;
}

#define BUG_ON(cond)                                                        \
	do {                                                                \
		if (cond) {                                                 \
			fprintf(stderr, "BUG at %s:%d: %s\n", __FILE__,     \
				__LINE__, #cond);                           \
			abort();                                            \
		}                                                           \
	} while (0)

#define min(a, b) ({ __typeof__(a) _a = (a); __typeof__(b) _b = (b); _a < _b ? _a : _b; })
#define max(a, b) ({ __typeof__(a) _a = (a); __typeof__(b) _b = (b); _a > _b ? _a : _b; })
#define min_t(t, a, b) min((t)(a), (t)(b))
#define max_t(t, a, b) max((t)(a), (t)(b))
#define clamp(v, lo, hi) min(max(v, lo), hi)
#define swap(a, b) do { __typeof__(a) _t = (a); (a) = (b); (b) = _t; } while (0)
#define DIV_ROUND_UP(n, d) (((n) + (d) - 1) / (d))
#define BITS_PER_LONG 64
#define BITS_TO_LONGS(n) DIV_ROUND_UP(n, BITS_PER_LONG)

static inline u64 div64_u64(u64 a, u64 b) { return a / b; }
static inline u64 div_u64(u64 a, u32 b) { return a / b; }
static inline u64 div64_u64_rem(u64 a, u64 b, u64 *rem) { *rem = a % b; return a / b; }

static inline u64 int_sqrt64(u64 x)
{
	u64 root = 0, bit = 1ULL << 62;

	while (bit > x)
		bit >>= 2;
	while (bit) {
		if (x >= root + bit) {
			x -= root + bit;
			root = (root >> 1) + bit;
		} else {
			root >>= 1;
		}
		bit >>= 2;
	}
	return root;
}

static inline bool test_bit(u64 nr, const unsigned long *map)
{
	return (map[nr / BITS_PER_LONG] >> (nr % BITS_PER_LONG)) & 1;
}
static inline void __set_bit(u64 nr, unsigned long *map)
{
	map[nr / BITS_PER_LONG] |= 1UL << (nr % BITS_PER_LONG);
}
static inline void __clear_bit(u64 nr, unsigned long *map)
{
	map[nr / BITS_PER_LONG] &= ~(1UL << (nr % BITS_PER_LONG));
}

static inline void *kshim_alloc(size_t size, bool zero)
{
	void *p = zero ? calloc(1, size) : malloc(size);

	BUG_ON(!p);
	return p;
}
#define vmalloc(size) kshim_alloc(size, false)
#define vzalloc(size) kshim_alloc(size, true)
#define kmalloc(size, gfp) kshim_alloc(size, false)
#define kzalloc(size, gfp) kshim_alloc(size, true)
#define kvmalloc(size, gfp) kshim_alloc(size, false)
#define vfree(p) free(p)
#define kvfree(p) free(p)
#define kfree(p) free(p)
#define sort(base, num, size, cmp, swap) qsort(base, num, size, cmp)

typedef int spinlock_t;
#define spin_lock_init(l) (*(l) = 0)
#define spin_trylock(l) (1)
#define spin_unlock(l) ((void)(l))
#define cpu_relax() do { } while (0)
struct mutex { int unused; };
#define DEFINE_MUTEX(name) struct mutex name
#define mutex_lock(m) ((void)(m))
#define mutex_unlock(m) ((void)(m))

struct list_head { struct list_head *next, *prev; };
#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define container_of(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))
static inline void INIT_LIST_HEAD(struct list_head *h) { h->next = h->prev = h; }
static inline void list_add_tail(struct list_head *e, struct list_head *h)
{
	e->prev = h->prev;
	e->next = h;
	h->prev->next = e;
	h->prev = e;
}
static inline void list_del_init(struct list_head *e)
{
	e->prev->next = e->next;
	e->next->prev = e->prev;
	INIT_LIST_HEAD(e);
}
#define list_first_entry_or_null(h, type, member) \
	((h)->next == (h) ? NULL : container_of((h)->next, type, member))

static inline u64 ktime_get_ns(void) { return kshim_now_ns; }
static inline u64 local_clock(void) { return kshim_now_ns; }
static inline u64 cpu_clock(int cpu) { return kshim_now_ns; }

#define module_param(name, type, perm)
#define MODULE_PARM_DESC(name, desc)

/* procfs: enough to call the measurement handlers directly */
struct proc_dir_entry { int unused; };
struct file { void *data; };
struct proc_ops {
	ssize_t (*proc_read)(struct file *, char *, size_t, loff_t *);
	ssize_t (*proc_write)(struct file *, const char *, size_t, loff_t *);
	void *proc_lseek;
};
#define default_llseek NULL
#define file_inode(f) (f)
#define pde_data(f) ((f)->data)
typedef unsigned int kuid_t;
#define init_user_ns 0
#define GLOBAL_ROOT_GID 0
#define make_kuid(ns, uid) (uid)
#define uid_valid(uid) (true)
static struct proc_dir_entry kshim_proc_entry;
#define proc_create_data(name, mode, parent, ops, data) (&kshim_proc_entry)
#define proc_set_user(entry, uid, gid) ((void)(entry))
#define proc_remove(entry) ((void)(entry))
#define copy_from_user(dst, src, n) (memcpy(dst, src, n), 0)

static inline char *strim(char *s)
{
	size_t n = strlen(s);

	while (n && (s[n - 1] == '\n' || s[n - 1] == ' '))
		s[--n] = '\0';
	while (*s == ' ')
		s++;
	return s;
}

static inline int scnprintf(char *buf, size_t size, const char *fmt, ...)
{
	va_list ap;
	int n;

	va_start(ap, fmt);
	n = vsnprintf(buf, size, fmt, ap);
	va_end(ap);
	return n < 0 ? 0 : ((size_t)n >= size ? (int)size - 1 : n);
}

static inline ssize_t simple_read_from_buffer(char *to, size_t count, loff_t *pos,
					      const void *from, size_t available)
{
	if ((size_t)*pos >= available)
		return 0;
	count = min(count, available - (size_t)*pos);
	memcpy(to, (const char *)from + *pos, count);
	*pos += count;
	return count;
}

/* The parts of nvmev.h that the FTL needs; the real header is kernel-only. */
#define _LIB_NVMEV_H
#include "nvme.h"

#define NVMEV_DRV_NAME "NVMeVirt"
#define NVMEV_INFO(string, args...) printk(KERN_INFO "%s: " string, NVMEV_DRV_NAME, ##args)
#define NVMEV_ERROR(string, args...) fprintf(stderr, "%s: " string, NVMEV_DRV_NAME, ##args)
#define NVMEV_ASSERT(x) BUG_ON((!(x)))
#define NVMEV_DEBUG(string, args...)
#define NVMEV_DEBUG_VERBOSE(string, args...)

#define KB(k) ((k) << 10)
#define MB(m) ((m) << 20)
#define GB(g) ((g) << 30)
#define BYTE_TO_KB(b) ((b) >> 10)
#define BYTE_TO_MB(b) ((b) >> 20)
#define BYTE_TO_GB(b) ((b) >> 30)
#define MS_PER_SEC(s) ((s)*1000)
#define US_PER_SEC(s) (MS_PER_SEC(s) * 1000)
#define NS_PER_SEC(s) (US_PER_SEC(s) * 1000)
#define pr_info_once(fmt, args...) printk(fmt, ##args)
#define LBA_TO_BYTE(lba) ((lba) << LBA_BITS)
#define BYTE_TO_LBA(byte) ((byte) >> LBA_BITS)

struct nvmev_request {
	struct nvme_command *cmd;
	uint32_t sq_id;
	uint64_t nsecs_start;
};

struct nvmev_result {
	uint32_t status;
	uint64_t nsecs_target;
	uint64_t result;
};

struct nvmev_ns {
	uint32_t id;
	uint32_t csi;
	uint64_t size;
	void *mapped;
	uint32_t nr_parts;
	void *ftls;
	bool (*proc_io_cmd)(struct nvmev_ns *ns, struct nvmev_request *req,
			    struct nvmev_result *ret);
};

struct nvmev_dev {
	struct {
		unsigned int cpu_nr_dispatcher;
	} config;
};
extern struct nvmev_dev *nvmev_vdev;

struct buffer;
void schedule_internal_operation(int sqid, unsigned long long nsecs_target,
				 struct buffer *write_buffer, size_t buffs_to_release);

#include "ssd_config.h"

#endif /* KSHIM_H */
