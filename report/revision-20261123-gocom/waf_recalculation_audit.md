# WAF 독립 재계산 감사 (고컴)

- 작성: 2026-11-23, 고컴. 스크립트는 `analysis/revision_gocom/waf_recalc.py`다. 기존 분석 스크립트를 쓰지 않고 새로 작성했다.
- 결과 파일: `result/revision-gocom-20261123/waf_recalc_{runs,phases,partitions,report_tables}.csv`
- **측정값과 계산값:**
  - host_pages, gc_pages, absorbed, evicted, nand_pages는 커널 모듈이 측정 구간 동안 센 **측정값**이다.
  - 모든 WAF는 이 카운터로 구한 **계산값**이다.

## 1. 정의 (소스로 확인)

| 항목 | 정의 | 코드 |
|---|---|---|
| host_pages | 측정 구간에 host가 쓴 페이지. SmartGC에서 GC 버퍼에 흡수된 쓰기도 포함한다 | `smartgc-src conv_ftl.c` `smartgc_absorb` 분기의 `host_page_writes++` (@5bd64c679 2527–2531행) |
| gc_pages | GC 복사로 NAND에 쓴 페이지 | `gc_write_page` |
| WAF | 1 + gc_pages / host_pages | 러너 summary, 승컴 `analysis/smartgc/compare.py:26` |
| nand_pages (SmartGC 빌드만) | host − absorbed + evicted + gc (파티션별) | 측정 파일 출력, `smartgc-src conv_ftl.c` (@5bd64c679 118–119행) |
| WAF_nand | nand_pages / host_pages. GC 버퍼가 없는 빌드는 WAF와 같다 | — |

## 2. 검사 범위: 35 run

- 고컴 mixFYF: revA 13회, revB 8회
- 승컴 mixY: fixed47, arm37, arm50, v6 (10월). sg-arm47, smartgc-eq8, SmartGC(재개), V4 (11월). v7 (10월)
- 고컴 mixY: v7 (10월). SmartGC, SmartGCQ, SG-Greedy, SG-ARM47 (11월)

## 3. 결과

| 검사 | 대상 수 | 불일치 | 비고 |
|---|---|---|---|
| T1: summary.txt 전체 host/gc 대 final-control.txt 파티션 합 | 35 | **0** | 페이지 수가 정확히 같다. WAF 차이 최대 5 × 10⁻⁷ (summary의 반올림) |
| T2: summary.txt 단계 WAF 대 단계 시작/끝 카운터 차분 | 371 단계 | **0** | host와 gc 모두 정확히 같다 |
| T3: 파티션별 WAF | 140 | — | 표만 만들었다 (`waf_recalc_partitions.csv`) |
| T4: SmartGC nand_pages, 모듈 출력 대 host − absorbed + evicted + gc 재계산 | 5 run × 4 파티션 | **0** | — |
| T5: 보고서 표의 수치 대 원시 재계산 | 38행 | **0** | 승컴 `compare.csv` (host_pages, WAF_nand), 고컴 `mixY_compare.csv`, `fyf_runs.csv` |

### SmartGC 계열 (계산값)

| run | WAF (1 + gc/host) | WAF_nand | absorbed | evicted |
|---|---|---|---|---|
| 승컴 SmartGC-EQ8 | 4.4984 | 4.4920 | 25,455,256 | 15,898,721 |
| 승컴 SmartGC | 11.0723 | 11.0180 | 74,929,604 | 18,248,705 |
| 고컴 SmartGC | 10.2490 | 10.1711 | 109,193,303 | 21,027,236 |
| 고컴 SmartGCQ | 4.7686 | 4.5846 | 432,037,543 | 50,443,290 |
| CAT/Greedy/iCAT 빌드 | WAF = WAF_nand | — | 0 | 0 |

## 4. 발견된 문제

**계산 스크립트 오류나 보고서 수치 불일치는 찾지 못했다.** 다만 해석에 주의할 점이 있다.

1. **같은 카운터를 두 경로로 읽은 일치**다. 독립 계측으로 검증한 것이 아니다. NVMeVirt 카운터 자체가 맞는지는 다른 근거로 확인한다.
   - FIO 구간에서는 fio가 끝낸 IO 수(revA·revB: 72,000,000)와 host_pages(72,001,978 등)가 0.003 % 안에서 맞는다. 남는 양은 파일시스템 메타데이터 쓰기다.
2. **SmartGC의 host_pages에는 흡수된 쓰기가 들어 있다.** 그래서 WAF(1 + gc/host)와 WAF_nand가 다르다. 논문에서 SmartGC는 **WAF_nand**로 비교해야 한다. 승컴 보고서는 그렇게 했다.
3. **summary.txt의 WAF는 소수점 6자리로 반올림된 값**이다. 보고서에 4자리로 쓰는 것은 문제가 없다.
4. **이번 범위 밖:** 승컴의 9월 mixR, mixA/C 결과와 resource-v124. 승컴이 따로 계산한 것으로, 고컴은 이번에 재계산하지 않았다. 필요하면 같은 스크립트에 경로만 추가하면 된다.
