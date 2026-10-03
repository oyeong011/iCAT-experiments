
## mixO-fixed50-tenhour-after37-20261003 — CAT37終了後 / CAT37종료후fixed50 10시간 사전등록
- 사용자명시명령 env MULT=20 VM_RUN=18000 bash script/mix-20260911.sh mixO fixed50 1. OLTP18000+Varmail18000,구간지정manual=1,30초원본/WAF. 현재37정상검증완료후자동시작,실패하면시작안함. 준비포함10h+2~5분,현재37예상완료10/3 09:36이후시작.
- 최신main922ec0d0 fetch/pull은로컬변경보존용독립icat-2 worktree에서수행. rootmix는최신자동NVMeVirt탐지본으로반영,기존localport백업 및현재37runner복사본보존. source/model/PCI/mount/module/global-lock검사를BASH_ENV가드로유지;최신측정스크립트수정없음.
- fixed50/arm50모듈SHA동일,커널7.0.0-31일치. 정책외준비/seed/Filebench함수는37과동일,서로다른MULT의mixO미사용변수차이기록. hostname/machine/source/modulehash/env/실제device/CPU는metadata와원본에보존.
- 캠페인result/mixO-fixed50-tenhour-after37-20261003. 실험끝나면exit0/error/요청IO/actualtime/stopflush/blockstat/counter검증,37및50결과만icat-2에선별commit/push;main다른로컬수정전송없음. 실패중단로그보존,동일호스트1실험,실SSD포맷/임의재부팅/강제reset없음.

- 최신main pull 충돌은독립publish트리에서최신코드/기존branch-only91개경로모두보존하여해결. merge fe13d4f4,root현재37정상측정유지. fixed50 waiterservice active;공유장치전용검사및push callback설정완료.
