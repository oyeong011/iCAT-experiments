# CAT37 정상 종료 후 OLTP→Varmail fixed50 10시간

현재상태 status.txt: CAT37 완료대기. CAT37 result.json이exit0/validated_saved_evidence일때만실행한다.

실행명령은 MULT=20 VM_RUN=18000 bash /home/oy/iCAT/script/mix-20260911.sh mixO fixed50 1. 최신main922ec0d0 자동NVMeVirt탐지/구간지정measurement_manual1 버전이며원본스크립트sha256metadata에기록했다. 결과/journal은최신스크립트의MIX_BASE/MIX_JOURNAL옵션으로캠페인분리. BASH_ENV가드는기존모델/시리얼/PCI/마운트/모듈보호유지,상위공유device.lock으로다른캠페인과장치공유금지. root의이전local스크립트백업을보존했고진행중37copy에는영향없다.

OLTP18000초+Varmail18000초,준비6GiB순차128k/3GiB무작위4k/seed20260907,반복1. 37실행의MULT1과50의MULT20은이mixO에서파일벤치시간/프로필/준비/계측에영향없음을함수본문비교로확인했다. fixed50/arm50모듈sha동일및커널7.0.0-31확인. 정책은50으로변경한다.

30초샘플은waf-series.csv와run/control-series.txt,최종검증은result.json/exit-code.txt/journal. 실제시간·쓰기량·카운터·프로필·prep오류·구간경계/flush/blockstat/host증거보존. 30초샘플독립반복으로세지않음. 실패하면보존하고중지.

37과50원본/메타/결과만독립icat-2 작업트리에선별복사하여commit/push한다. main과관련없는로컬변경은전송하지않음. 90MiB초과파일은원본을유지하고publish복사본만64MiB분할+SHA256/목록으로전송한다. 결과push상태publish.exit. user서비스icat-mixO-fixed50-after37-20261003은logout/reboot자동복구하지않음.
