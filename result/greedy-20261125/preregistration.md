# greedy-20261125 사전 등록: Online Greedy 비교 (심사 의견 M3, 승컴)

- 작성: 2026-11-25, 실행 전. **명시적 실행 승인 전에는 본 실험을 시작하지 않는다.**
- 지금 돌고 있는 추가 ablation 큐(`revision-additional-ablation`, 11-26 00:50쯤 끝남)가 끝나기 전에는 시작할 수 없다. 장치 잠금과 `busy()` 검사가 이를 막는다.
- 금지 사항:
  - Random Selection, Random Search, Periodic Switching을 다시 돌리거나 추가하지 않는다
  - 기존 E1, revC, revD, ablation 결과를 덮어쓰지 않는다
  - 실행 중인 프로세스를 멈추지 않는다

## 1. 정책

| 정책 | 모듈 | SHA256 | 내용 |
|---|---|---|---|
| greedy-online | `buildoutput/nvmev-greedy-online.ko` (greedy-src, `ICAT_VARIANT=8`) | 4df03c90dad0efb4… | 45개 arm을 1회씩 평가한 뒤, 매 판단 구간마다 할인 없는 누적 평균 WAF가 가장 낮은 arm을 고른다 |
| greedy-v4 (조건부) | `buildoutput/nvmev-abl-v4.ko` | b35775057f2e7dc6… | revD-v4, abl-v4와 같은 파일 |

- 구현 상세는 `implementation_review.md`, 소스 차이는 `greedy-src.diff`에 있다.

## 2. 통제 조건 (revD, ablation과 같음)
- 러너: `runner-greedy.sh` = `runner-abl.sh` 사본. 정책 목록, 모듈 경로, 라벨만 바꿨다 (`port.diff`).
- 부하:
  - mixFYF: FIO-Fast(test4, ×3) 1800 s → YCSB-A(SQLite 250k, load+run 1800 s) → FIO-Fast 1800 s
  - test.dat는 계속 유지한다
- 초기화: insmod (memmap 4G+8G, cpus=1,2, icat_seed) → mkfs, mount nodiscard → Table-3 준비 (randseed 20260907) → 카운터 0 확인
- seed:
  - FIO hot/warm/cold = 20260910/20261010/20261110 + rep
  - icat_seed = 2026111400 + rep
  - revD, ablation과 rep별로 같다. 그래서 같은 seed끼리 짝지은 비교를 할 수 있다.
- 반복: n = 3. 단기 실행은 정책마다 120 s 1회이고, 합산하지 않는다.

## 3. V4 대조군: 재사용 결정 규칙 (사전 고정)
- **판단 시점:** 추가 ablation 큐가 끝난 직후, greedy 큐를 시작하기 전에 판단한다.
- **판단 자료:** `abl-v4`(11-25, n=3)와 `revD-v4`(11-24, n=3)의 전체 WAF Welch 95 % CI.
- **규칙:**
  - CI가 0을 포함하고 평균 차이의 절댓값이 0.02 이하이면 → 날짜에 따른 배치 효과가 작다고 본다.
    - 대조군은 시간상 가장 가까운 `abl-v4`다 (`control.txt` = abl-v4).
    - 큐는 `queue-order.greedy-only.txt` (greedy 3회)다.
  - 그 밖의 경우 → 같은 배치에서 V4를 새로 돌린다.
    - 대조군은 `greedy-v4`다 (`control.txt` = greedy-v4).
    - 큐는 `queue-order.with-v4.txt` (greedy 3 + V4 3, rep 블록마다 `random.Random(20261126 + rep)`로 섞은 순서)다.
- **한계:** 재사용하더라도 greedy는 abl-v4보다 약 하루 늦게 실행된다. 보고서에 그대로 적는다.
- 판단 결과와 계산값은 `control-decision.txt`에 남긴다.

## 4. Random Selection
- 승컴에는 mixFYF Random Selection 결과가 없다. 고컴 revA-random n=3만 있다.
- 다시 돌리지 않으므로 **Greedy와 Random을 직접 비교할 수 없다** (호스트가 다르다).
- 그래서 각 호스트 안에서 V4 대비 차이만 나란히 보고한다:
  - 승컴 Greedy − V4
  - 고컴 Random − V4
- 두 차이를 합산하거나 서로 빼지 않는다.

## 5. 지표

| 지표 | 원천 |
|---|---|
| 전체, 단계별 WAF (control 첫 줄 + 파티션 합 일치 확인) | `phase-*-start/end.txt`, `stopped.txt` |
| arm별 평가 창 수 (`evaluated`), arm별 선택 횟수 (`next`) | `kernel.log` sample |
| 최종 선택 arm (파티션별 마지막 `next`) | 같음 |
| 초기 탐색 비용: 45개 arm을 모두 처음 볼 때까지의 창 수와 host, gc, WAF | 같음 |
| 정책 변경 횟수: `select` 카운터 (next ≠ evaluated인 창 수) | 같음 |
| 학습 경과 시간: `learner_ns` (ktime, CPU 시간 아님) | 같음 |
| Greedy 규칙 검증: 커버 이후 모든 창에서 `next` = 로그로 다시 계산한 argmin(누적 Σgc/Σhost, Q16 floor, 동률이면 작은 번호)인지. 불일치 0이어야 한다 | 같음 |
| YCSB 요청, 성공률, SQLITE_FULL, FIO 오류, 커널 오류, 모듈 SHA256 | `ycsb-run-B.txt.gz`, `phase-*.json`, `kernel.log`, `environment.txt` |

- **주 대비:** Greedy − V4 (전체 WAF, 단계 C WAF), 같은 호스트 안에서만 비교한다.
- **통계:**
  - 평균 ± SD, t 95 % CI, Welch CI와 p, Hedges' g
  - 같은 seed끼리 짝지은 차이 (rep 1–3, 대응 t, df 2)
- **n = 3의 한계:** df ≈ 2–4라 검정력이 낮다. CI가 0을 포함하면 "차이를 확인하지 못했다"로 쓰고, 동등성을 주장하지 않는다.
- 분석 스크립트: `analysis/revision/greedy_analysis.py` → `result/greedy-20261125-analysis/`

## 6. 유효성 (매 run, 하나라도 실패하면 큐 정지, 다음 run을 자동으로 시작하지 않음)
- 모듈 SHA256을 insmod 전에 확인
- exit 0, 단계 A/B/C 완료, FIO 오류 0
- YCSB 실패 0, SQLITE_FULL 0
- 커널 BUG/WARNING/Oops 0
- WAF 두 경로 일치
- 언로드, umount 완료
- **단기 실행 추가 확인:** Greedy 단기 실행에서 첫 45창이 서로 다른 45개 arm인지 확인한다 (120 s 안에 커버하지 못하면 커버 전 창들만 확인한다).

## 7. 시간
- greedy만: 단기 1 × 7.6분 + 본 3 × 91.6분 ≈ **4.7시간**
- V4 포함: 단기 2 × 7.6분 + 본 6 × 91.6분 ≈ **9.4시간**
- 가장 빨리 시작할 수 있는 시각: 11-26 00:50쯤 (추가 ablation 큐가 끝난 뒤)
