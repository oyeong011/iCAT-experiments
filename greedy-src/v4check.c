#include <stdio.h>
#include <stdint.h>
#include <assert.h>
#include <stdbool.h>
#define WATGC_V2_K_N 4
#define WATGC_V2_SCALE_N 5
#define WATGC_V2_RATIO_N 3
#define WATGC_V2_ARM_N 60
#define WATGC_V2_ARM_LO 15U
#define WATGC_V2_ALLOWED (~0ULL << WATGC_V2_ARM_LO & (~0ULL >> (64 - WATGC_V2_ARM_N)))
static uint32_t watgc_v2_neighbour(uint32_t arm, uint32_t slot)
{
	int ki = arm / (WATGC_V2_SCALE_N * WATGC_V2_RATIO_N);
	int si = (arm / WATGC_V2_RATIO_N) % WATGC_V2_SCALE_N;
	int ri = arm % WATGC_V2_RATIO_N;
	int d = (slot & 1) ? 1 : -1;
	uint32_t n;

	if (slot / 2 == 0) ki += d; else if (slot / 2 == 1) si += d; else ri += d;
	if (ki < 0 || ki >= WATGC_V2_K_N || si < 0 || si >= WATGC_V2_SCALE_N ||
	    ri < 0 || ri >= WATGC_V2_RATIO_N)
		return WATGC_V2_ARM_N;
	n = (ki * WATGC_V2_SCALE_N + si) * WATGC_V2_RATIO_N + ri;
	return (WATGC_V2_ALLOWED >> n) & 1 ? n : WATGC_V2_ARM_N;
}
static uint64_t watgc_v2_grow(uint64_t set)
{
	uint64_t out = set;
	uint32_t i, s, n;

	for (i = 0; i < WATGC_V2_ARM_N; i++) {
		if (!((set >> i) & 1))
			continue;
		for (s = 0; s < 6; s++) {
			n = watgc_v2_neighbour(i, s);
			if (n < WATGC_V2_ARM_N)
				out |= 1ULL << n;
		}
	}
	return out;
}
int main(void){ uint32_t s,n; int got17=0;
 for(s=0;s<6;s++){ n=watgc_v2_neighbour(32,s); printf("%u ",n); if(n==17)got17=1; } printf("\n");
 assert(got17);                                   /* 32=(k7,s25,r16) -> k4 neighbour 17 */
 for(s=0;s<6;s++) assert(watgc_v2_neighbour(17,s)==60 || watgc_v2_neighbour(17,s)>=15);  /* never a k=2 arm */
 assert(watgc_v2_neighbour(17,0)==60);            /* k4 -> k2 is excluded */
 assert(__builtin_popcountll(WATGC_V2_ALLOWED)==45);
 assert(watgc_v2_grow(1ULL<<32) == ((1ULL<<32)|(1ULL<<17)|(1ULL<<47)|(1ULL<<35)|(1ULL<<31)));
 puts("v4 neighbour check OK"); return 0; }
