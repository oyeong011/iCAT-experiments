# drift50-20261126 사전 등록: 변화 감지 문턱 50 % (M6, 승컴)

- 작성: 2026-11-26, 실행 전. 큐와 인프라는 `result/batchG-20261126/`에 있다. 원시 로그는 이 폴더의 `raw/`에 쌓인다.

## 정정: 지시의 "V4 = 15 %"
- V4의 변화 감지 문턱은 **25 %**다: `WATGC_V2_DRIFT_Q16 16384` (revD-src/conv_ftl.h:75).
- 15 %는 후보 제거 문턱(`WATGC_V2_ELIM`)이다.
- 그래서 비교 대상은 **12.5 % (고컴 revE-drift12) / 25 % (V4) / 50 % (신규)**다.

## 모듈

| 정책 | 모듈 | SHA256 | 빌드 |
|---|---|---|---|
| drift50 | `buildoutput/nvmev-drift50.ko` | 8196ed9b7dccc537… | revD-src(소스 수정 없음), `ICAT_VARIANT=4 ICAT_EXTRA=-DWATGC_V2_DRIFT_Q16=32768ULL` |
| bg-v4 (같은 배치 대조군) | `buildoutput/nvmev-abl-v4.ko` | b35775057f2e7dc6… | revD-v4, abl-v4와 같은 파일 |

- abl-v4 대비 objdump 정규화 차이는 1줄이다: `shl $0xe` → `shl $0xf` (감지 비교식의 ×16384 → ×32768). 파일: `../batchG-20261126/build/objdump-drift50-vs-abl-v4.diff`
- 감지 조건 (conv_ftl.c 567–577):
  - 정착 상태이고 current = best인 창에서 |sample − reference| > reference × 50 %가 3창 연속이면 리셋한다.

## 실행 중 검증 (`drift-check.py`, 실패하면 큐 정지)
- 모든 `WATGC_V2 reset` 줄이 커널과 같은 정수식에서 편차 > 50 %를 만족해야 한다.
- 음성 대조: abl-v4 rep1(25 %)에 같은 검사를 적용했다. 편차 42 % 리셋이 잡혀 FAIL이 나온다. 즉 이 검사는 25 % 모듈과 50 % 모듈을 구분한다.

## 대조군과 재현성
- revD-v4와 abl-v4의 배치 재현성 기준(±0.02)이 미달했다.
  - 그래서 기존 V4와 합치지 않는다. **같은 배치 V4 3회(bg-v4)**를 함께 돌린다.
  - 이 bg-v4는 Greedy GC 비교와 같이 쓴다.
- 고컴 revE-drift12(12.5 %)는 호스트가 다르다 (고컴, revC-src).
  - 합산하거나 직접 빼지 않는다.
  - 각 호스트 안에서 V4 대비 차이만 나란히 보고한다: 승컴 drift50 − bg-v4, 고컴 drift12 − revE-v4.

## 순서와 seed
- 대상: drift50, greedygc, bg-v4. 정책마다 n=3.
- rep 블록마다 `random.Random(20261126 + rep)`로 순서를 섞었다 (`queue-order.registered.txt`).
- seed는 revD와 같다: FIO 20260910/20261010/20261110 + rep, icat_seed 2026111400 + rep.
- 단기 실행 120 s 1회씩은 합산하지 않는다.

## 지표
1. 전체·단계별 WAF
2. 감지(리셋) 횟수와 시점 (단계별, 파티션별)
3. 재탐색 시작 시점 (= 리셋 시각)
4. 복원 후보 수 (리셋 직후 active 수)
5. 재정착 시간 (리셋 → 같은 파티션 settled)
6. 탐색 비용 (evaluated ≠ best 창의 host 비중, WAF)
7. 회복 시간 (11-23 사전 정의, 보조)

- 주 대비: drift50 − bg-v4 (전체, 단계 C). Welch 95 % CI, Hedges' g, 같은 seed 짝 차이.
- WAF만으로 해석하지 않는다. 감지 시점과 재정착 과정을 함께 표로 낸다.
