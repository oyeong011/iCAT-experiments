# 두 번째 실험 컴퓨터(icat-2) 작업 지시서 — Codex용

목적: 11개 전환 워크로드마다 **고정 CAT 60개 전부**의 순위를 매긴다(현재는 17개만 측정됨).
원래 컴퓨터는 iCAT-v4 반복·ablation을 맡고 있으므로, 이 컴퓨터는 **고정 CAT 측정만** 한다.

## 순서 (각 단계 성공 확인 후 다음으로)
1. `DUAL_BOOT_GUIDE.md` 6-1 ~ 6-5 수행 (커널 7.0.0-31, `setup-new-machine.sh` 두 번).
2. `bash script/validate-new-machine.sh` → 마지막 줄이 **PASS**여야 한다.
   FAIL이면 **멈추고** 결과(`result/validate-*`)를 브랜치 `icat-2`로 push한 뒤 사용자에게 보고. 측정 큐를 돌리지 않는다.
3. `EXPERIMENT_LOG.md`에서 "QUEUE33" 사전 등록 항목을 확인하고, 실행 환경(호스트명, 커널, CPU, 메모리, 모듈 SHA256)을 그 아래에 추가 기록.
4. 실행: `nohup bash script/gh-queue33-fullsweep.sh > ~/queue33.out 2>&1 &`
   - 1단계: 11 워크로드 × 60 arm, 1배 길이 (1회 약 18분, 총 6~8일)
   - 2단계: 워크로드별 상위 5개를 3배 길이로 재측정
5. 진행 확인: `tail ~/queue33.out`, `ls result/mix-20260911/*/SUSPECT.txt`

## 지켜야 할 것
- push는 **브랜치 `icat-2`에만** (스크립트가 자동으로 함). `main`에 push 금지 — 원래 컴퓨터가 병합한다.
- `script/mix-20260911.sh`, 모듈 소스, 분석 스크립트를 **수정하지 않는다**. 문제가 생기면 멈추고 보고.
- 실패한 run은 지우지 않는다. `SUSPECT.txt`가 생기면 `echo 3 | sudo tee /proc/sys/vm/drop_caches` 후
  `fio --version; sqlite3 --version; java -version` 확인, 계속 깨져 있으면 재부팅 후 큐 재실행(완료된 run은 자동으로 건너뜀).
- 재부팅 후에는 4번 명령만 다시 실행하면 이어서 진행된다.
- 실험일지 규칙은 `AGENTS.md` 그대로 따른다.
