
## QUEUE33 / queue33-icat2-20261002 — CODEX_HANDOFF f299c51e 실행환경 추가
- hostname oy-B550M-DS3H, machine_id f4f3e77cb5bf4a08ab288227cf288de0, kernel7.0.0-31. CPU/RAM과 module SHA는 handoff 환경 및 campaign module-sha256.
- 사용자 nvme1n1 지시: 동적모델/시리얼/PCI검사 유지, 기대 /dev/nvme1n1, 실nvme0n1제외. 기존root mix/source/analysis 추가수정없음. 캠페인runner복사본은결과/journal라우팅만변경. 측정정의/prepare/workload/seed유지.
- 순서: 기존진행1회정상종료 -> validate3정책600초각각35~40분 -> PASS만 queue33. 고정11종×60×1회x1(약6~8일) -> 각상위5 x3VM_RUN900. 동일호스트run1개씩. 실패검증시stop, 삭제/overwrite/강제reset/자동재부팅금지.
- 원본queue의crosshost summaryskip/rm-rf/gitadd-A는안전wrapper에서제외. 같은호스트유효결과만재사용,공유device.lock유지,icat-2 전용독립publishworktree에campaign증거만commit/push. main/root로컬수정업로드안함.
- run prereg: 고유label-armNN-rep1(x3),policy/modulehash/CPUenv1,2/rep1seed20260911,20261011,20261111 및 workloadtemplates/campaignmeta고정. 실행별시작/종료journal,exit0/fioerror0/요청IO/YCSBreturn/stopflush/block-statvalidity검증. 다른호스트순위합침은QUEUE33의workload별overlap검증없이하지않음.
- 명령: systemd user icat-handoff-f299c51e-20261002가validate후queue33 queue.py실행. campaign result/queue33-icat2-20261002. 종료/수행량/오류는status/results/journal 후속기록.

- QUEUE33 wrapper 추가검증/출판: SUSPECT/준비요청량6GiB+3GiB/도구전후/전체YCSB요청완료/단일호스트확인. 커밋작성자는Codex(icat-2),task-local-c옵션만사용. 계측runner/source/analysis 불변.

- 2026-10-02 14:36:00 START mixO-arm00-rep1; module nvmev-arm00.ko; MULT=1 VM_RUN=300, rep1; source/CPU/module/device metadata recorded; runner output routing only changes.

### mix-20260911 mixO arm00 — started 2026-10-02T14:36:00+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm00.ko`.
- Command: `bash script/mix-20260911.sh mixO arm00`; evidence `result/mix-20260911/mixO-arm00/`.

- Finished 2026-10-02T14:37:21+09:00; mixO arm00 exit=143; evidence `/home/oy/iCAT/result/queue33-icat2-20261002/mixO-arm00-rep1`; cleanup attempted.

- 사후 오류기록: 검증3개 모두env.sh의RESULT_DIR readonly재대입으로exit1, WAFNone. 성능검증아님. 실패보고publisher의git sparse-add예외 처리 중 동일폴더queue.py 이름충돌로 queue가예기치않게실행됨(관측parentpublish.py PID59909 -> runner PID59942). 이후parent정지/TERM으로준비중run중단,exit143/카운터epoch0active0. 결과정상풀제외,전체로그보존. 정상unmount/rmmod완료,실SSD변경없음. queue파일run-fixed-campaign.py로rename,explicitmain/PASS/HALTED이중guard추가,측정재시작없음. publisher sparse-add수정후필수실패증거만icat-2전송.
