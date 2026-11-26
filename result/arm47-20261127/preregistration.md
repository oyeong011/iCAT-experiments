# arm47-20261127 사전 등록: 고정 Arm 47 반복 실행 (Robustness, 승컴)

- 작성: 2026-11-27 00:35. batchG 큐가 끝나기 전, 실행 전에 썼다.
- 지시: 11-27 "승컴 긴급 지시 — batchG 최종 완료 및 고정 Arm 47 Robustness 검증" 작업 B.
  - 이 지시는 이전의 "고정 arm 47 반복 금지"를 **Arm 47에 한해** 명시적으로 해제한다.
  - Arm 17, 50 등 다른 arm은 여전히 금지다.

## 1. 기존 결과 (덮어쓰지 않음)
- `origin/report/data-validity-20261124` (bba0886e9)의 `result/revA-20261114/raw/mixFYF-arm47-rep1` — **고컴**, 2026-11-14, n=1.
  - 전체 WAF 1.987355 (A 1.774412 / B 1.026571 / C 2.278243)
- 승컴 main에는 mixFYF arm47 결과가 없다.

## 2. 조건 대조 (기존 n=1 vs 이번)

| 항목 | 기존 (고컴 revA) | 이번 (승컴) | 같음? |
|---|---|---|---|
| 모듈 | `buildoutput/nvmev-arm47.ko` 9fde0ea49892b1c8… | 같은 파일, sha256 9fde0ea49892b1c8… (vermagic 7.0.0-31-generic) | ✅ |
| 러너 | `runner-revA.sh` | `runner-arm47.sh` = `runner-batchG.sh` 사본. batchG 러너는 revA 러너와 라벨, 경로, 정책 목록만 다르다 (`port.diff`). arm47 경로(모듈 `arm[0-5][0-9]` 분기, icat_seed 미전달, 초기 arm 47 확인)는 같다 | ✅ |
| 부하 | mixFYF: FIO-Fast(test4) 1800 s → YCSB-A (SQLite 250 000 records, load+run 1800 s) → FIO-Fast 1800 s | 같음 | ✅ |
| 초기화 | insmod (memmap 4G+8G, cpus=1,2) → mkfs, mount nodiscard → Table-3 준비 (randseed 20260907) → 카운터 0 확인 | 같음 | ✅ |
| FIO seed | hot/warm/cold = 20260910/20261010/20261110 + rep | 같은 규칙, rep 1–3 | ✅ |
| icat_seed | 고정 arm이라 모듈에 전달하지 않는다 | 같음 | ✅ |
| **호스트** | **고컴 (AMD)** | **승컴 (Intel)** | ❌ 이 PC에서는 맞출 수 없다 |

- 호스트가 다르므로 기존 n=1을 이번 3회와 **합산하지 않는다.**
- 이번 결과는 "승컴 Arm 47 n=3"으로 보고한다. 기존 고컴 n=1은 옆에 참고로만 둔다.
- 승컴 V4와의 비교는 **같은 호스트 안에서만** 한다. batchG bg-v4 n=3이 가장 가까운 배치다.
  - 다만 다른 배치이므로 배치 효과 한계를 적는다 (V4 배치 재현성 규칙 미충족 이력이 있다).

## 3. 실행
- 순서: smoke 120 s × 1 → rep1 → rep2 → rep3. 결과는 `result/arm47-20261127/raw/`에 둔다.
- 매 run마다 `check-run.py`를 돌린다. 이상이 하나라도 있으면 큐를 멈춘다. 매 run마다 push한다.
- `cpu_check`는 이번 배치에서도 `unavailable`이다. CPU를 측정하지 않았다는 뜻이다 (`result/batchG-20261126/cpu-check-investigation.md`).
- 예상 시간: 7.6분 + 3 × 91.6분 ≈ 4.7시간. 00:45쯤 시작하면 05:30쯤 끝난다.

## 4. 지표와 통계
- 전체 WAF와 단계 A/B/C WAF. 원시 카운터 두 경로(control 첫 줄, 파티션 합)로 재계산한다.
- YCSB 성공률, SQLITE_FULL, FIO 오류, 커널 오류, 모듈 SHA256, seed, 커널 로그의 `Fixed CAT init ... arm=47`.
- n=3 평균, SD, t 95 % CI.
- 기존 고컴 n=1과의 차이는 기술 통계로만 보고한다. 호스트가 다르므로 검정하지 않는다.
- 참고 비교: 승컴 Arm 47 − 승컴 bg-v4 (Welch, Hedges' g). 다른 배치라는 한계를 같이 적는다.
- CI가 넓거나 0을 포함하면 "차이를 확인하지 못했다"로 쓴다.
