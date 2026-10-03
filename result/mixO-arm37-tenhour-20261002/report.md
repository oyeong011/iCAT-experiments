# OLTP → Varmail / 기본 CAT arm37 / 약10시간

사용자 명시 요청의 단일 실험이다. OLTP18000초(5시간) 뒤 Varmail18000초(5시간)를 같은 모듈·파일시스템·계측 epoch에서 연속 실행한다. 준비는 측정 전6GiB순차preset+3GiB무작위seed20260907. 프로필생성/삭제/동기화는 측정에 포함되므로 실제 길이는10시간보다조금길수있다. 다른큐는실행하지않는다.

30초간격 원본은 mixO-arm37-rep1/control-series.txt, 계산값은 waf-series.csv다. active=1이면서host_pages>0인행의 cumulative_waf=1+gc_pages/host_pages. 초기준비active0행은WAF값을비워측정으로세지않는다. elapsed는실제phaseA시작시간기준이며샘플timestamp를그대로남긴다. 30초행은독립반복아니다.

상태status.txt, 모듈/호스트/머신/source/커널/옵션/seed/device는metadata.json과environment-before.txt 및run environment/device에기록했다. 장치는매로드시모델·시리얼·PCI검사로안전하게식별한NVMeVirt /dev/nvme1n1이다. 실저장장치 /dev/nvme0n1은대상으로사용하지않는다. 기존공유device.lock/모듈/마운트보호유지. root mix/source/analysis추가변경없음. 캠페인runner는결과/journal라우팅만다르고VM_RUN18000을명시한다.

실행서비스 icat-mixO-arm37-tenhour-20261002.service. 준비포함약10시간2~5분. 종료후result.json에서실제구간시간·쓰기량·WAF·검증·실패원인·exit을확인한다. 실패/중단원본보존. 서비스는임의재부팅/강제reset/반복재시작하지않으며user Linger=no라서로그아웃/재부팅시지속보장은없다.

현재호스트단독새측정이다. 과거호스트와섞지않고, 앞선legacyGreedy동등성검증FAIL을PASS로바꾸지않는다. arm37은기본CAT(k7,scale100,ratio7)이며관측된최소CAT라고부르지않는다.

## 실제 종료 상태

2026-10-03 00:43:33 시스템전체OOM으로Filebench가종료되어10시간실험실패. OLTP약1시간8분관측, Varmail미시작. 마지막부분누적WAF1.332891은10시간결과아님. rawkernel/systemd/exit1/시계열보존. 후속CAT50/v4는실패조건으로시작되지않음.
