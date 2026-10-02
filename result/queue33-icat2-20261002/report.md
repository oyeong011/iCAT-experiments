# QUEUE33 — 두 번째 PC 고정 CAT 전체 측정

CODEX_HANDOFF f299c51e에 따른 고정 CAT 전용 캠페인. mixO, mixF, mixJ, mixP, mixB, mixD, mixK, mixH, mixG, mixL, mixQ의11종을각60개 x1 측정한후, 각관측상위5개를x3/MULT3/VM_RUN900으로확인한다. 총715회예정. 역사적실행시간+120초준비 가정 stage1약177.1시간(7.4일), stage2약40.0시간. 현재PC에서변동한다. 먼저validation3회PASS가필수다.

상태는 ../handoff-f299c51e-20261002/status.txt, 실행시작후status.csv/results.csv/inventory.csv/rank-reference.csv/convergence.csv에저장된다. 주실행서비스는icat-handoff-f299c51e-20261002.service. 기존22조건v4큐는현재1회정상종료후중지되고후속측정은없다. validationFAIL이면CAT큐시작하지않고증거만icat-2에push한다.

장치는현재 /dev/nvme1n1이고각로드마다모델/시리얼/PCI안전검사로검증한다. /dev/nvme0n1 실제SSD는금지한다. 공유lock유지. 기존root측정스크립트/모듈소스/분석스크립트추가수정없음. 로컬에서이미허용된안전포트본runner를복사해결과/journal라우팅만변경했다. QUEUE33원본의crosshost-summaryskip,실패run삭제,gitadd-A는적용하지않았다. 캠페인코드변경과해시/provenance는metadata/journal에명시했다.

결과는호스트별분리. 3개정책1%PASS는전체60/manual계측동등성증명아님. 원래호스트와워크로드별중복arm의WAF중앙차/순위상관을검토하기전에는v4와합치지않는다. x1의60순위와x3의상위5순위는각각pool크기와함께보고하며,x3미측정55개를확정하지않는다. 30초시계열은독립반복아니다. 초기학습비용포함v4와비교할때정의명시.

검증: exit0,준비/시작0,stop0/flush안정,파티션합,fio오류/요청IO,YCSB작업완료/Return,Filebench프로필길이,runner의hostbytes-blockstatassert. 실패면보존하고중지한다. 재부팅이나강제reset은자동실행하지않는다. 로그아웃/재부팅은피해야하며user서비스의Linger=no로로그아웃후지속보장은없다.

GitHub전송은독립worktree의icat-2에서이캠페인과필수검증증거만명시선택해commit/push한다. main과기존로컬수정은전송하지않는다. 신규워크로드는아직정의되지않았으며이번11종이후자동추가하지않는다.
