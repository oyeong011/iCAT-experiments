
### mixO-fixed37-chunked-20261003 preregistration
Command: env MULT=20 VM_RUN=900 VM_CHUNKS=20 bash script/mix-20260911.sh mixO fixed37 1
Expected 10h plus preparation/process overhead. Only virtual nvme1n1, global lock; previous failed37 preserved, blocked50/v4 remain stopped. OLTP restart preserves reuse filesets, module and measurement counters; no resets between chunks. 30s samples. Validate exit0, twenty OLTP IO Summary durations900, Varmail18000, preparation fio error0/requested bytes, zero-start/stop counters and blockstat assertion. Environment/module/source metadata adjacent; module build provenance unchanged from earlier current-kernel build, exact upstream build equivalence unconfirmed. Publish complete/failed evidence to icat-2.

## 2026-10-03 22:25 KST 원본 재검증

실행은 20:53:30에 exit=0으로 완료. 처음 검증기는 IO Summary 끝의 초 단위를 찾았으나 실제 Filebench 형식은 줄 앞 타임스탬프여서 잘못 실패 처리했다. Running→IO Summary 시간차로 OLTP 20회(각 약901초), Varmail 1회(약18001초)를 확인했다. 최초 판정과 검증기 사본을 before-revalidation-* 및 launch-before-validation-fix.py로 보존했다. revalidate.py는 원본만 읽고 실험을 실행하지 않는다.

최종 누적 WAF=2.1215335398442443. OLTP 구간 WAF=1.294790, Varmail 구간 WAF=2.336186. host_bytes=14139532218368. 구간 실제 시간 OLTP18098초, Varmail18005초. 준비 fio 오류0/요청량 일치, zero-start, stop/final 및 파티션 카운터 합 일치 확인. 원본 runner exit0은 block-stat/host_bytes 검사 통과를 포함하며 별도 독립 측정으로 과장하지 않는다. 30초 수집 CSV는 준비 포함1205행이며 독립 반복이 아니다. 종료 후 마운트와 nvmev 모듈 해제 확인. 다른 호스트/연속 OLTP 실행과 동일 조건으로 합치지 않는다.
