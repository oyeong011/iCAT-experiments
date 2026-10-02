# QUEUE33 실행 전 발견한 문제

- 배포mix runner는nvme0n1고정. 현재nvme0n1=실SSD,nvme1n1=NVMeVirt. 모델검사에걸려실행불가;보호우회금지.
- queue33은summary존재만으로타호스트복사결과를완료취급함. 새호스트60개전체측정이되지않음.
- rm -rf 실패run을삭제함:사용자보존규칙과충돌.
- git add -A/자동commit/push는기존무관변경까지포함함. 브랜치icat-2이더라도원본변경전체업로드불가.
- 3정책1%PASS는전체60/명시계측동등성증명이아님. 호스트구분유지.

handoff는mix runner/module/analysis수정금지와문제시멈추고보고를명시. 기존로컬수정은보존하며추가수정/QUEUE33실행하지않음. 현재oldqueue부모만정지하고현재run정상종료후validate를진행한다. 외부push는필수검증FAIL시icat-2에실패증거만좁혀전송가능.
