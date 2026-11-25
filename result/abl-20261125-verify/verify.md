# 승컴 abl-20261125 고컴 독립 검증 (2026-11-26 04:50)

- 원시 자료: origin/main `result/revision-additional-ablation/` (72da7384d). 읽기만 했다.
- 도구: `analysis/online_greedy/og_audit.py` (OG_OUT=result/abl-20261125-verify). 결과: `og_audit.md`, `runs.csv`, `stats.csv`, `contrasts.csv`.
- 유효성: 9/9 유효. 확인 항목: exit 0, 모듈 해시 등록, 부하 해시, FIO·icat seed, YCSB 실패 0, SQLITE_FULL 0, 커널 오류 0, WAF 두 경로 일치.
- 승컴 `contrasts.csv`, `conclusion.md`와 비교: 평균, SD, Welch Δ, CI가 소수 넷째 자리까지 일치한다.
  - OffBundle − V4: +0.1241 [+0.0730, +0.1753], 단계 C +0.2168. Holm p 0.028 (승컴 값).
  - NoDiscount − V4: −0.0038 [−0.0644, +0.0569]. 구분되지 않는다.
- 승컴 checks.tsv의 CPU 점검은 "unavailable (FileNotFoundError)"였다. 이 배치에는 CPU 점유율 확인 자료가 없다. 기록만 하고 무효 사유로 쓰지 않는다.
  - 승컴 사전 등록(preregistration.md)의 유효성 기준에는 CPU 점유율 점검이 없다. 따라서 이 누락은 사전 등록 위반이 아니다.
- 재현성 대비 (abl-v4 − revD-v4, 다른 배치 같은 호스트)는 승컴이 사전 기준(±0.02) 미통과로 판정했다. 고컴도 이 대비를 판정에 쓰지 않는다.
- 논문 반영: 표 10 배치 F.
