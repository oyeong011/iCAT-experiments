# 두 번째 실험 컴퓨터(icat-2) 작업 지시서 — Codex용

목적: 11개 전환 워크로드마다 **고정 CAT 60개 전부**의 순위를 매긴다(현재는 17개만 측정됨).
원래 컴퓨터는 iCAT-v4 반복·ablation을 맡고 있으므로, 이 컴퓨터는 **고정 CAT 측정만** 한다.

## 2026-10-02 수정 (Codex 보고 반영) — 먼저 읽을 것
Codex가 멈추고 보고한 문제 4가지를 저장소에서 고쳤다. **로컬 수정은 버리고 저장소 버전을 쓴다.**
1. `/dev/nvme0n1` 고정 → `mix-20260911.sh`, `gh-fio.sh`, `gh-filebench.sh`가 모델명 `CSL_Virt`로 가상 SSD를 찾는다(이 PC에서는 nvme1n1). 실제 SSD(nvme0n1)는 건드리지 않는다.
2. 다른 컴퓨터 결과를 건너뜀 → queue33은 `result/icat2-fullsweep/`에만 쓴다(원래 컴퓨터 결과와 섞이지 않음, 17개 겹치는 arm도 새로 잰다).
3. 실패 디렉터리 삭제 → 삭제하지 않고 `-failed-<시각>`으로 이름만 바꿔 보존.
4. `git add -A` → `result/icat2-fullsweep`와 `EXPERIMENT_LOG-icat2.md`만 올린다. 실험일지도 이 PC 전용 파일에 쓴다.

재시작 순서:
```bash
cd ~/iCAT
git stash push -u -m "codex-local-before-fix"   # 로컬 수정·결과 보존(지우지 않음)
git pull
bash script/validate-new-machine.sh            # PASS 확인
nohup bash script/gh-queue33-fullsweep.sh > ~/queue33.out 2>&1 &
```
- 이전에 시작한 `mixed-cat-full-20261002`(54일 큐)와 `queue33-icat2-20261002`, `handoff-*` 자동 진행 도구는 **중지**하고 다시 켜지 않는다(결과 파일은 보존). 이 PC는 고정 CAT 60개 측정만 한다(v4는 원래 컴퓨터).
- 잘못 시작됐던 `mixO-arm00-rep1` 준비 I/O 결과는 사용하지 않는다.
- stash에 실험 결과 파일이 들어갔다면 `git stash show -p`로 확인 후 `result/` 아래 결과만 별도 폴더로 꺼내 보존해도 된다.

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
