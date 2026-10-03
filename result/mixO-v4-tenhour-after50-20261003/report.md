# OLTP→Varmail iCAT-v4 約10h / 약10시간

큐순서는CAT37→fixed50→onlinev4. fixed50의정상검증과공유device.lock해제후v4를시작한다. MULT20 VM_RUN18000,OLTP5시간+Varmail5시간,구간지정manual계측,30초누적WAF. 초기학습비용포함,초기샘플임의제외없음. source922ec0d0/준비/프로필/호스트/장치/seed/측정경계는앞선50과동일,정책만v4.

현재status.txt는대기상태. 실행후waf-series.csv와run/control-series.txt,최종result.json/exit-code/journal에저장. 결과검증후37·50·v4를icat-2에선별push. kernel4partition샘플/호스트counter/flush/block-statassert/FIO준비요청량/실제두구간시간확인. 실패중단보존. 30초샘플은독립반복아니다.
