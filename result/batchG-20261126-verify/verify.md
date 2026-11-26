# 승컴 batchG-20261126 (M3 Greedy GC, M6 감지 문턱 50 %) 고컴 독립 검증 (2026-11-27 02:10)

- 원시 자료: origin/main 2ccac44b7 의 `result/batchG-20261126/raw/` (bg-v4), `result/greedygc-20261126/raw/`, `result/drift50-20261126/raw/`. 읽기만 했다(scratchpad로 git archive).
- 도구: 고컴 `analysis/online_greedy/og_audit.py` (승컴 batchG_analysis.py는 쓰지 않음). 출력: `og_audit.md`, `runs.csv`, `stats.csv`, `contrasts.csv`, `arms.csv`.
- Holm과 drift50 리셋 조건은 runs.csv와 kernel.log에서 별도 계산했다(아래 값).

## 유효성: 9/9 유효
- exit 0, 모듈 sha256이 `result/batchG-20261126/modules.sha256`에 등록됨, 부하 파일 해시, FIO seed, YCSB 실패 0, SQLITE_FULL 0, 커널 오류 0, FIO 오류 0, WAF 두 경로 일치.
- greedygc의 icat_seed_ok=False는 학습기가 없는 빌드라 seed 인자가 없기 때문이다. 유효성 기준이 아니다.
- CPU 점유율 확인 자료는 없다(승컴 checks.tsv "cpu_check=unavailable"). 승컴 사전 등록 유효성 기준에 CPU 항목이 없으므로 무효 사유가 아니다.

## 통계 (같은 호스트, 같은 배치, 각 n=3)

| 대비 | 지표 | Δ | Welch 95 % CI | p | Holm (4개 주 대비) | 승컴 값과 |
|---|---|---|---|---|---|---|
| Greedy GC − V4 | 전체 WAF | +0.5189 | [+0.4633, +0.5744] | 0.00032 | 0.0013 | 일치 (소수 넷째 자리) |
| Greedy GC − V4 | 단계 C WAF | +0.7078 | [+0.5882, +0.8274] | 0.0013 | 0.0038 | 일치 |
| 감지 50 % − V4 (25 %) | 전체 WAF | +0.0183 | [−0.0445, +0.0812] | 0.459 | 0.831 | 일치 |
| 감지 50 % − V4 (25 %) | 단계 C WAF | +0.0418 | [−0.0877, +0.1714] | 0.415 | 0.831 | 일치 |

- 판정
  - M3: iCAT-v4가 legacy Greedy GC보다 WAF가 낮다. Holm 후에도 0.05 미만이다.
  - M6: 감지 문턱 50 %는 25 %와 구분되지 않는다. "구분되지 않음"은 동등하다는 뜻이 아니다.
- drift50 리셋: kernel.log의 `WATGC_V2 reset` 11건이 모두 |sample − reference|/reference > 0.5였다(최소 0.614). 승컴 drift-check와 일치한다.
- 승컴 결론에 적힌 불리한 결과는 그대로 둔다. Greedy GC가 FIO 쓰기 p99 지연은 더 낮았다. 고컴은 지연을 재계산하지 않았다.
- 고컴 revE 결과(감지 12.5 %, +0.072)는 다른 호스트와 배치이므로 합치지 않는다.
- 상태: 고컴 검증 일치. 집컴 검증은 별도로 요청되어 있다(승컴 verification-request.md).
