# iCAT 검증 실험 — 기술 요약 (2026-09-15 기준, 진행 중)

## 1. 문제 정의

NAND 플래시 SSD의 FTL은 free block이 부족할 때 victim block을 선택해 유효 페이지를 재배치(GC)한다. 성능 지표는 write amplification factor

$$\mathrm{WAF}=\frac{P_{host}+P_{GC}}{P_{host}}$$

로, $P_{host}$는 호스트 쓰기 페이지 수, $P_{GC}$는 GC 재배치 페이지 수이다. 본 실험은 FTL 내부 카운터로 이를 직접 측정한다.

비교 대상 victim 선택 정책:

| 정책 | victim 선택 규칙 |
|---|---|
| Greedy | $\arg\min_{line} vpc$ (유효 페이지 수 최소) |
| CAT (Cost-Age-Time, Fig.7 변형) | $\arg\min_{line} \dfrac{vpc}{ipc \cdot \mathrm{AgeLevel}(age)}$. $\mathrm{AgeLevel}$은 line의 마지막 무효화 이후 경과 시간을 $k$단계 계단 함수로 변환; 경계 $b_i = \mathrm{scale}\cdot b_i^{0}$, 출력값은 $18$부터 $18\cdot\mathrm{ratio}$까지 선형. 파라미터 $(k,\mathrm{scale},\mathrm{ratio})\in\{2,4,7,10\}\times\{25,50,100,200,400\%\}\times\{4,7,16\}$, 60조합(arm 0–59) |
| iCAT (WATGC_V2) | 60 arm을 discounted UCB($\gamma\approx0.9995$, $c=0.25$)로 온라인 선택. window = 64 GC 또는 65,536 host pages(256 MiB) 중 먼저 도달; window마다 관측 WAF를 reward로 갱신, 다음 arm 선택. FTL 파티션(4개) 독립 |

연구 질문: (Q1) 고정 CAT의 최적 파라미터가 워크로드에 의존하는가. (Q2) iCAT이 사전 지식 없이 워크로드별 최적 고정 CAT에 근접하는가. (Q3) 워크로드가 시간에 따라 변할 때 iCAT이 고정 CAT보다 낮은 WAF를 얻는가.

## 2. 실험 환경

- NVMeVirt conventional SSD 에뮬레이터, 물리 8 GiB(memmap 4G–12G), 논리 namespace 7.6 GiB, dispatcher/worker CPU 1,2. 커널 7.0.0-31-generic. ext4, `nodiscard`(TRIM 없음).
- 소스: 원 저자 저장소 commit 7236149. 정책·FTL 코드 무변경. 본 머신에서 insmod 시 order-6/9 연속 페이지 할당 실패가 발생해 `ssd_init`의 배열 6곳(`kmalloc→kvmalloc`)과 `io.c`의 work queue(`kzalloc→kvzalloc`)만 수정. 모든 모듈 SHA256은 `result/gh-repro-20260914/modules.sha256`에 기록.
- 계측 두 방식. (i) 원 저자 방식: 모듈 로드 후 파티션당 100 GC warmup 이후 누적 카운터, rmmod 시 출력. (ii) 명시 방식: `/proc/nvmevirt_measurement`에 `start`/`stop`을 써서 구간을 지정. 두 방식 모두 `host_bytes = Linux block write sectors × 512`를 run마다 검증.
- 반복: fio는 `randseed` 고정 후 seed를 +1/+2한 3변형; 앱 워크로드는 동일 조건 3회. 아직 (n)이 1인 셀이 다수이므로 표준편차는 완성 후 보고.

## 3. 워크로드

| 이름 | 정의 | 선정 이유 |
|---|---|---|
| test2 | fio 4 KiB random write, 6 GiB 파일, hot 1 GiB + cold 5 GiB, 합계 10k IOPS, 600 s | 2단 skew 기준선 |
| test3 | hot 512 MiB(6k IOPS) / warm 1.5 GiB(3k) / cold 4 GiB(1k) | 3단 skew; hot 재기록 주기 22 s |
| test4 | test3와 동일 배치, IOPS ×4 (24k/12k/4k) | 재기록 주기 ×1/4 → `scale` 감도; 사전 sweep 편차 최대(27.7%) |
| test5 | 앞 2 GiB 32k / 뒤 4 GiB 8k IOPS, 300 s 후 반전 | 공간적 hot 이동 |
| sqlite-a/b | YCSB 0.17.0 → SQLite(WAL, page 4 KiB), 400만 record, 100만 op, zipfian; a=read/update 50/50, b=95/5 | 실제 DB; 사전 sweep 편차 27.5%/19.6%. 원 저자와 동일하게 run 중 4 s 간격 `drop_caches` |
| oltp / varmail | Filebench 1.5-alpha3 (oltp: 512 MiB×10 파일; varmail: 원 저자 HEAD 설정 150,000 파일) | 앱 워크로드. Filebench 1.5의 `fileset_resolvepath` strlcpy 크기 버그(_FORTIFY_SOURCE abort)를 1줄 수정 |
| rocksdb-a | YCSB → RocksDB | GC 재배치 0(순차 대용량 쓰기 + 파일 단위 삭제)으로 정책 무관 → 비교에서 제외 |
| mix A–Q (14종) | §5 참조 | 시간적 워크로드 변화 |

준비(preconditioning)는 모든 run에서 동일: 새 namespace, 6 GiB 순차 쓰기, 전체 6 GiB에 3 GiB 4 KiB random(10k IOPS, seed 고정), sync. 명시 계측은 이 이후 `start`.

## 4. 결과 — 단일 워크로드 (원 저자 계측 방식)

평균 WAF, 괄호는 반복 수. 굵게 = 행 최솟값.

| 워크로드 | Greedy | arm10 (test4 최악) | arm37 (HEAD 기본) | arm47 (test4 최적) | arm50 (6-wl minimax) | iCAT |
|---|---:|---:|---:|---:|---:|---:|
| test2 | 1.594(1) | 1.593(1) | 1.446(1) | 1.420(1) | **1.415**(1) | 1.591(1) |
| test3 | 2.034(3) | 2.038(3) | 1.729(5) | **1.714**(3) | 1.715(2) | 2.015(4) |
| test4 | 2.186(3) | 2.231(3) | 1.938(4) | **1.739**(3) | 1.787(3) | 1.950(4) |
| test5 | 1.631(2) | 1.629(2) | 1.594(4) | **1.585**(2) | **1.585**(2) | 1.610(4) |
| sqlite-a | 1.503(1) | 1.509(1) | 1.272(3) | **1.159**(1) | 1.164(1) | 1.342(3) |
| sqlite-b | 1.281(1) | 1.282(1) | 1.113(3) | **1.070**(1) | 1.071(1) | 1.104(3) |
| oltp | 1.634(1) | 1.671(1) | 1.522(3) | 1.465(1) | **1.427**(1) | 1.592(3) |
| varmail | 4.762(1) | 4.970(1) | 4.623(3) | **3.537**(1) | 3.954(1) | 4.927(3) |

관찰:
1. **Q1(파라미터의 워크로드 의존성)은 지지된다.** 최적 arm이 워크로드별로 다르다(사전 sweep: test3 arm33, test4 arm47, sqlite-a arm17, oltp arm49). 최악 arm은 모든 워크로드에서 $k=2$이며 Greedy와 ±1% 이내 — $k=2$, 경계 720 s는 재기록 주기(≤262 s)보다 길어 age 정보가 사실상 소거되기 때문이다.
2. 그러나 **단일 고정 arm(arm50)이 8개 워크로드 전부에서 최적 대비 ≤4% 이내**다. 즉 "워크로드별 튜닝이 필요하다"는 전제는 정량적으로 약하다(최대 이득 4%).
3. **Q2는 기각된다.** iCAT은 모든 워크로드에서 최적 고정 CAT 대비 4–25% 높은 WAF를 보이며, test2/test3/test5에서는 Greedy와 1% 이내다. test4에서 3-seed 평균 iCAT 2.001 vs arm47 1.774(명시 계측, 표준편차 <0.001)로 재현성이 높다.
4. 측정 타당성: Greedy test4는 원 저자 기록 2.223 대비 2.203(−0.9%)으로 재현. arm37은 1.869 대비 1.938(+3.7%)로 커널·Age 초기값 차이 가능성이 있으나 순위는 보존.

## 5. 결과 — 시간적 워크로드 변화 (mix, 명시 계측)

설계(모두 동일 준비 후, phase 사이 모듈·학습기 리셋 없음):

| mix | phase A → B (→ C) | 검증 대상 |
|---|---|---|
| A | test4 → sqlite-a (600k rec, 4M op; fio 파일 유지) | 앱 전환 |
| B | sqlite-a → test4 | 앱 전환(역순) |
| C / D | test3 → test4 / test4 → test3 | 재기록 시간축 ×4 / ×1/4 |
| J | sqlite-a → sqlite-b (동일 DB, load 없음) | 쓰기 비율 변화 |
| G | test4(½ payload) ∥ sqlite-a 동시 | 공간적 혼합 |
| K | test4 hot 512 MiB → hot 128 MiB, IOPS 동일 | locality 변화 |
| L | (test4 60 s, test3 60 s) × 5 | 주기적 변화 |
| M | test3 배치, IOPS 10k→50k 5단계 × 120 s | 점진적 변화 |
| Q | test4(½) → 300 s idle → test4(½) | age 진행만 있는 구간 |
| O / P / H / F | oltp→varmail / sqlite-a→oltp / test3→test4→sqlite-a / test4→varmail | 보조 |

이전 설계(phase A 파일 삭제 후 phase B)는 TRIM 부재로 6 GiB가 FTL 관점에서 유효 상태로 잔존해 phase B WAF가 2.1–3.4로 왜곡되었기에 A–Q에서는 파일을 유지한다.

현재 완료: mix A seed 1 (6정책).

| mix A | Greedy | arm10 | arm37 | arm47 | arm50 | iCAT |
|---|---:|---:|---:|---:|---:|---:|
| phase A test4 | 2.252 | 2.262 | 1.974 | **1.774** | 1.813 | 2.000 |
| phase B sqlite-a | 2.920 | 2.871 | 1.711 | 1.519 | **1.499** | 2.484 |
| 전체 | 2.421 | 2.418 | 1.907 | **1.709** | 1.733 | 2.123 |

phase 전환으로 최적 arm이 47→50으로 바뀌지만 차이는 1.3%이며, iCAT은 phase B에서 고정 CAT 3종 대비 45–65% 높다. Q3는 현 시점에서 지지되지 않는다(seed 2,3 및 mix B–Q 진행 중).

## 6. iCAT 열세의 원인 분석

`WATGC_V2 sample` 커널 로그(window마다 arm, 관측 WAF, best, settled 기록)를 분석했다.

- **탐색 미완료가 아니다.** phase 3600 s(long) 실험에서도 파티션 0의 370 window 중 `settled=1`은 2회, best arm은 37→0→18→49→33→36→48→46으로 이동. 600 s에서 3600 s로 늘려도 WAF 개선 없음(1.969→1.952).
- **reward 잡음이 arm 간 차이를 압도한다.** 동일 워크로드(test4, 정상 상태) 내에서 8회 이상 관측된 16개 arm의 window WAF: 동일 arm 내 최대–최소 폭 평균 **0.385**, arm 평균값 간 최대 차 **0.098**. 즉 SNR ≈ 0.25. window(64 GC ≈ 10 s)가 hot/cold line 정리 국면에 따라 GC 비용이 크게 달라지는 시간 규모보다 짧다.
- 결과적으로 iCAT의 정상 상태 WAF는 60 arm의 (거의) 균등 혼합에 수렴하며, 이는 관측된 "Greedy보다 약간 좋고 고정 CAT보다 나쁨"과 일치한다.
- 시사점: (a) window를 ≥16배 늘려 잡음 분산을 $1/\sqrt{n}$로 낮추거나, (b) 사전 지식으로 $k=2$ 15개 arm을 제거해 탐색을 25% 줄이거나, (c) 선택 후 다수 window 유지(dwell) 등 학습기 수정이 필요하며, 이는 별도 버전으로 기록한다.

## 7. 타당성 위협

- 단일 에뮬레이터, 단일 기하. 실제 장치·다른 OP 비율에서의 일반화는 미검증.
- 대부분 셀 $n\le3$; 앱 워크로드는 run 간 변동이 큼(oltp iCAT 3회: 1.49/1.65/1.64). 통계적 유의성 주장 없음.
- 원 저자 sweep(60 arm)은 커널 6.8, 생성시각 Age, 1회 실행이며 그 소스는 커밋되어 있지 않다. 본 실험의 arm 라벨(최악/최적/견고)은 그 sweep 기준이며, 본 환경 재측정에서 순위가 일부 바뀔 수 있다(예: oltp에서 arm50이 arm47보다 낮음).
- varmail은 원 저자 HEAD 설정(150,000 파일)이 sweep 설정(24,000)과 달라 절대값 비교 불가. rocksdb는 제외.
- mix의 phase 길이(600 s)는 iCAT의 1회 sweep 길이(≈600 s)와 같다. 그러나 §6의 3600 s 결과가 길이 가설을 기각하므로 결론에는 영향이 없다.
- 무인 실행 중 발견·수정한 항목(webproxy/videoserver `run` 지시 부재, videoserver fileset 축소, YCSB 로그 압축)은 모두 일지에 시각과 함께 기록.

## 8. 현재 결론

1. CAT 파라미터의 최적값은 워크로드에 따라 다르지만, 견고한 단일 arm(arm50)의 손실은 ≤4%로 작다.
2. 제공된 iCAT 구현은 어떤 워크로드·계측 방식·phase 길이에서도 최적 고정 CAT을 이기지 못하며, Greedy 대비 이득도 워크로드에 따라 0–14%로 불안정하다.
3. 원인은 reward의 SNR 부족으로 인한 비수렴이며, 학습기 설계 수정으로 해결 가능한 성격이다. 수정 후 목표: 최적 고정 CAT 대비 손실 < arm50의 손실(4%).

전체 원본 로그·스크립트·모듈 해시: https://github.com/oyeong011/iCAT-experiments (실행 일지 `EXPERIMENT_LOG.md`, 집계 `analysis/summary.py`).
