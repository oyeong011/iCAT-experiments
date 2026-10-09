# 90-minute FIO → Varmail → OLTP CAT ranking

Validated 2/60; unmeasured or invalid 58. Same host, one run per arm.
Rank = 1 + count(validated fixed CAT WAF < target WAF). Missing arms widen the rank range.
This is the 90-minute workload ranking, not the previous 10-hour mixX ranking.
Small observed differences are not evidence of statistical superiority. 30-second samples are not independent repeats.

| Measured rank | Arm | WAF | Possible rank among 60 |
|---:|---|---:|---|
| 1 | arm00 | 3.269211 | 1–59 |
| 2 | arm01 | 3.315207 | 2–60 |
