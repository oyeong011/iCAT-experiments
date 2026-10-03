
## mixO-arm37-tenhour-20261002 — 用户指定 / 用户優先 / 사용자 최우선10시간 실행 사전등록
- 명시지시: OLTP→Varmail 기본CAT arm37 총약10시간. 정책1개/run1개만실행. 두구간18000초씩,VM_RUN=18000 MULT1 rep1. 매30초누적WAF원본/계산값저장. 다른큐공유없음. 준비포함예상10시간+2~5분.
- source/host/kernel/modulehash/빌드옵션/seed/CPU/준비/device: campaign metadata/environment-before/source-status와run environment/device/preset/prepare/profile. 원래호스트legacy검증FAIL을PASS로바꾸지않고현재호스트단독자료로보존. 현재가상장치전용nvme1n1검사,실nvme0n1금지.
- 명령systemduser icat-mixO-arm37-tenhour-20261002: python3 campaign/launch.py. root mix스크립트/모듈source/analysis 불변;복사runner는output/journal라우팅만변경. 공유device.lock/모듈/마운트보호유지.
- 판정exit0,FIO준비error0/요청량,기본arm37module/hash,zero-start/stop/flush/counterpartsum/hostbytes-blockstat,FilebenchIO Summary각구간18000초. 실패중단보존,동일초기화반복아닌연속두구간. 30초샘플독립반복아님. 초기화·구간전환쓰기포함누적WAF.
- 증거result/mixO-arm37-tenhour-20261002,rawcontrol-series.txt/waf-series.csv 및kernel/profile/filebench/start/stop/exit. 종료actualtimes/쓰기량/오류/정리상태는launch후속journal/result.json기록.

### mix-20260911 mixO arm37 — started 2026-10-02T23:33:55+09:00

- Phase A fio test4 fixed payload (58982400000/29491200000/9830400000 bytes hot/warm/cold, 24k/12k/4k IOPS) → rm test.dat (no discard) → Phase B YCSB sqlite workloada (0 records, 0 ops, drop_caches 4s during run). Age=LAST_INVALIDATION. Module `nvmev-arm37.ko`.
- Command: `bash script/mix-20260911.sh mixO arm37`; evidence `result/mix-20260911/mixO-arm37/`.

- 조건확인: 사용자요청 MULT20 VM_RUN18000 대비 실제 MULT1 VM_RUN18000. mixO는Filebench2구간만실행하며MULT는미사용FIOpayload/OPS0/디렉터리명에만영향. 실제OLTP run18000 및향후Varmail동일VM_RUN,준비고정,manual sysfsY 및zero-start확인. 기능상측정조건동일하나환경변수문자열차이명시;실행중변수수정/재시작없음.

- Finished 2026-10-03T00:43:33+09:00; mixO arm37 exit=1; evidence `/home/oy/iCAT/result/mixO-arm37-tenhour-20261002/mixO-arm37-rep1`; cleanup attempted.

- 사후복원: 2026-10-03 00:43:33 service OOM-kill, peak10.9G,runnerexit1. 10시간미완료/OLTP만약4063초관측/Varmail미실행. 마지막부분WAF1.332891은10h최종값아님. 실패원본보존,후속50/v4미실행조건으로실패status/result복원. 가상모듈해제됐으나shutdown mount잔존확인,새실험미시작.

- 정리추가: 실행프로세스없음/fuser사용자없음/가상모듈미존재확인후정상sudo umount성공,shutdown마운트해제. 강제reset/재부팅/실SSD변경없음.
