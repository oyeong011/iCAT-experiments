#!/usr/bin/env python3
"""20-phase order for mixY over the given workload letters: never the same letter twice in a row; each step takes the least-used
transition (cur -> next), then the least-used letter, then alphabetical order. Deterministic. Usage: mixy-seq.py F S V [P] [W]"""
import sys, itertools
L = sys.argv[1:]; seq = [L[0]]; tc = {}; lc = {x: 0 for x in L}; lc[L[0]] = 1
while len(seq) < 20:
    cur = seq[-1]; nxt = min((x for x in L if x != cur), key=lambda x: (tc.get((cur, x), 0), lc[x], x))
    tc[(cur, nxt)] = tc.get((cur, nxt), 0) + 1; lc[nxt] += 1; seq.append(nxt)
print(' '.join(seq))
