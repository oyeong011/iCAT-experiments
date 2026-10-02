# iCAT 논문·구현 점검과 실험 재설계

작성: 2026-09-03. 대상: 논문 최종본 초안 + `meendragon/iCAT` @ `8542e25`.

## 1. 기존 결과 재분석

`result_e1`, `result_e2`, `result` 의 dmesg 로그를 다시 계산한 값이다 (모두 `runtime=600`, 1회 실행).

| workload | policy | scale | ratio | WAF |
|---|---|---:|---:|---:|
| test2 | greedy | – | – | 1.5560 |
| test2 | cat-fig7 | 100 | 7 | 1.5104 |
| test3 | greedy | – | – | 2.0264 |
| test3 | cat-fig7 | 100 | 7 | **1.7898** |
| test3 | cat-fig7 | 25 | 7 | 1.8390 |
| test3 | cat-fig7 | 50 | 7 | 1.8236 |
| test3 | cat-fig7 | 200 | 7 | 1.8068 |
| test3 | cat-fig7 | 400 | 7 | 1.8206 |
| test3 | cat-fig7 | 100 | 4 | 1.8259 |
| test3 | cat-fig7 | 100 | 7 | **1.8150** |
| test3 | cat-fig7 | 100 | 16 | 1.8073 |

읽히는 사실은 세 가지다.

1. **CAT은 두 워크로드 모두에서 Greedy를 이긴다.** test2 −2.9%, test3 −11.7%. 그림 1의 기본 신호는 있다.
2. **α 곡선은 평탄하지 않고 내부에 최소점이 있다.** test3에서 α=1이 최소(1.7898), 양쪽으로 상승. 스프레드 2.7%.
3. **그런데 같은 설정을 두 번 돌린 값이 1.7898과 1.8150으로 1.4% 벌어진다.** 굵게 표시한 두 행은 `scale=100, ratio=7`로 완전히 동일한 구성이다. 즉 **관측된 효과 크기(2.7%)가 미반복 run-to-run 편차(1.4%)와 같은 자릿수**다. 현재 데이터로는 α 곡선의 모양을 주장할 수 없다. `experiment.md`가 요구한 3회 반복이 실제로는 수행되지 않았다.

### 1.1 Age 시간축이 디바이스 규모와 맞지 않는다

로그의 geometry: FTL 인스턴스당 `lines=8192`, `line-size=256KiB`(64 pages), `SSD_PARTITIONS=4` → 전체 32,768 lines.
test3 600초 동안 `gc_count=156,751` → 초당 261 line erase.

    line pool 1회전 시간 ≈ 32,768 / 261 ≈ 125 초

즉 이 8 GiB 에뮬레이터에서 line의 평균 체류 시간은 약 125초다. Fig. 7 원본 경계 `{10,20,45,90,180,360}`의 **상위 두 구간(180s, 360s)은 α=1에서도 거의 도달하지 않고, α=2(720s)·α=4(1440s)에서는 전혀 도달하지 않는다.** α≥2 조건은 서로 다른 age 함수가 아니라 *잘린 같은 함수*를 비교한 셈이고, α 사이의 차이는 사실상 하위 경계(10·20·45초)만 움직인 결과다. α 탐색 범위를 25~400%가 아니라 **5~100% 쪽으로 확장**해야 논문이 주장하려는 "경계 시간축이 워크로드 갱신 주기에 맞아야 한다"를 실제로 관측할 수 있다.

## 2. 논문에서 고쳐야 하는 것

### 2.1 Age 정의가 본문과 구현에서 다르다 (최우선, 나머지 전부의 전제)

본문은 Age를 **"마지막 무효화 이후의 경과시간"** 으로 6곳 이상에서 정의하고, 시간적 지역성 논증 전체를 그 위에 세운다. 구현은 `line->created_at_ns` = **line의 첫 페이지 기록 시각**이고, 무효화로 갱신되지 않는다(`experiment.md §0`, 마지막 커밋 "no reset age").

이 차이는 표기 문제가 아니라 메커니즘의 방향 문제다. 점수 `vpc/(ipc×AgeLevel)`는 작을수록 우선 선택이므로 **AgeLevel이 클수록 빨리 회수**된다. 계속 갱신되는 hot line은 생성 시각 기준 age가 단조 증가하므로 시간이 갈수록 회수 우선순위가 올라간다 — 본문이 설명하는 "최근 무효화된 블록은 회수를 미룬다"의 정반대다.

→ 결정 사항. 본문을 구현에 맞춰 "line 생성 이후 경과시간"으로 고치고 논리를 다시 쓰거나, 구현을 본문에 맞춰 last-invalidation age로 바꾸거나. **실험으로 판정할 수 있게 두 정의를 모두 빌드 가능하게 만들어 두었다(§3).**

### 2.2 기법의 정체성이 세 가지로 갈린다

- 초록/서론: `BAT-GC`, "bandit-based"
- Ⅱ.3, Ⅴ 서두: 표 기반 **Q-learning**, state를 age 분포·무효화 간격·VPC 분포·GC 복사율로 이산화
- Ⅴ.5.1~5.2: state 언급 없이 **K개 후보의 최근 가중 보상 평균** = 사실상 non-stationary bandit
- 이름: `BAT-GC` / `iCAT` 혼용

셋 중 하나로 정해야 한다. §5.2의 bandit을 채택하면 Ⅱ.3의 state 이산화 서술은 통째로 죽은 텍스트가 된다. 반대로 Q-learning을 채택하면 state 정의·Q-table 크기·수렴 시간을 실험으로 보여야 한다. 컨트롤러 자원 제약(Ⅱ.4)과 §5.3.1의 `O(K)` 주장은 bandit 쪽과 훨씬 잘 맞는다.

### 2.3 보상 정의가 두 곳에서 다르다

- Ⅱ.3: `r_t = -GCPageWrites_t / HostPageWrites_t`
- Ⅴ.5.1.4: `R_t = -WAF_t = -(1 + G_t/H_t)`

최적점은 같지만 표기는 통일해야 한다. 그리고 5.1.4의 WAF 수식은 `\frac{H_t+G_t}{H_t}` 와 `1+\frac{G_t}{H_t}` 가 등호 없이 나란히 놓여 깨져 있다.

### 2.4 점수의 방향이 뒤집혀 있다

Ⅱ.2 끝에 "GC는 비용-편익 점수가 가장 큰 블록을 희생 블록으로 선정한다"고 쓰여 있는데, 구현과 `experiment.md §2.2`의 CAT 점수 `vpc/(ipc×AgeLevel)`는 **작을수록** 우선이다. CB(클수록 좋음)와 CAT(작을수록 좋음)을 한 문단에서 섞었다.

### 2.5 표 1(SmartGC Q-table 메모리)의 계산 근거가 없다

1 Tb die = 5,461 blocks → 104 MB 라는 수가 어떻게 나오는지 본문에 없다. 이 숫자가 "블록 단위 학습 대신 정책 단위 학습"이라는 본 논문의 두 번째 기여 전체를 지탱하므로, state 차원 수 × 이산화 구간 수 × 항목 크기까지 식으로 밝혀야 한다.

### 2.6 워크로드 구성이 초록과 실험계획서에서 다르다

초록·서론은 YCSB-A/F 기반 RocksDB·SQLite와 Filebench varmail·oltp. `experiment.md`는 fio + SQLite + RocksDB + Filebench **fileserver**. 하나로 맞춰야 한다. 참고로 이 머신의 가용 RAM은 약 2 GiB라 2.5~3 GiB DB는 page cache와 충돌한다 — DB 크기를 줄이거나 `posix_fadvise`/`O_DIRECT` 구성이 필요하다.

### 2.7 기계적 수정 (마지막에 한 번에)

- 참고문헌 번호가 어긋난다. SmartGC가 Ⅲ.2에서 [8], Ⅳ.2에서 [7]. Kang 등이 [6]과 [8]. References 목록에는 항목이 4개뿐인데 본문은 [1]~[9]를 인용한다. 학회 규정상 인용은 오름차순, 모든 항목은 본문에 1회 이상 인용되어야 한다.
- 키워드 `MuWrite Amplification` 오타. `Multi-` 흔적으로 보인다.
- Ⅴ의 번호 체계가 `1.1`과 `5.1.2`로 섞여 있다.
- Ⅴ 뒤 "1. 동적 워크로드와 희생 블록 선정 정책의 실시간 조정 / 워크로드 특성이 시간에 따라 끊임없이 변하여 매 순간" 문단이 3회 중복되고 미완성이다.
- Ⅵ 실험, Ⅶ 결론이 비어 있다.
- 초록의 X%, 본문의 X/Y/M/X_max 자리표시자가 그대로다.
- 그림 1·2가 아직 존재하지 않는다 — 지금 돌릴 실험이 그것이다.

## 3. 구현에 추가한 것

`nvmevirt_test/` 에 다음을 넣었다. 기존 victim-selection 경로와 점수 함수는 건드리지 않았다.

1. **Age 정의를 컴파일 타임 선택으로.** `NVMEVIRT_AGE_MODE=CREATE|LAST_INVAL`. `LAST_INVAL`은 `struct line.last_invalid_ns`를 `mark_page_invalid()`에서 갱신하고 age를 `now - last_invalid_ns`로 계산한다. §2.1을 실험으로 판정하기 위한 것이다.
2. **구간별 WAF.** host page `NVMEVIRT_WAF_WINDOW_PAGES`(기본 262,144 = 1 GiB)마다 `GC window: seq=… WAF=…` 한 줄을 찍는다. 기존에는 rmmod 시점의 누적 WAF 하나뿐이라 (a) 튜너의 reward, (b) 그림 5의 action timeline, (c) Ⅳ.1이 주장하는 "워크로드 내부 국면 변화" 중 어느 것도 관측할 수 없었다. 경계 판정은 2의 거듭제곱 마스크라 write path에 나눗셈이 없다.
3. **Victim 특성 히스토그램.** 선택된 victim의 raw age를 원본 Fig. 7 경계로 버킷팅한 개수, 평균 vpc, 평균 age를 rmmod 시점에 dump. Greedy 빌드에서도 기록되므로 정책 간 victim 분포 비교(실험 5)가 된다. 여기서 victim이 한 버킷에 몰려 있으면 age 축 자체에 변별력이 없다는 뜻이고, 그러면 §5의 모든 ablation은 노이즈를 재는 것이 된다 — **α 스윕보다 먼저 확인할 것.**
4. **α 범위 확장.** `NVMEVIRT_CAT_SCALE_PCT`에 5, 10을 추가 (§1.1).
5. K(구간 개수) 축은 아직 넣지 않았다. α와 강도 축의 효과가 반복 실험으로 확인된 뒤에 추가하는 편이 싸다.

빌드는 GREEDY/CAT × CREATE/LAST_INVAL 네 조합 모두 경고 없이 통과했다.

## 4. 스크립트

`/home/meen` 하드코딩을 전부 제거했다. `script/env.sh`가 스크립트 위치에서 경로를 유도하고, `MNT_DIR`·`DEV`·`MEMMAP_*`·`NVMEV_CPUS`는 환경변수로 덮어쓸 수 있다. `.fio` 파일도 `${FIO_TARGET}`, `${FIO_RUNTIME}`으로 파라미터화했다.

    script/build.sh <tag> [MAKE_VAR=VAL ...]   # buildoutput/nvmev-<tag>.ko
    script/run.sh <tag> <workload> [rep]       # preset + workload, dmesg 구간 저장
    script/matrix.sh a|b [reps]                # 스윕 (아래)
    analysis/parse.py result/*.log             # 요약 CSV + 평균/표준편차
    analysis/parse.py --windows result/*.log   # 구간별 WAF 시계열

`run.sh`가 mount에 `-o nodiscard`를 붙인다. 기존 스크립트는 ext4 기본 마운트라 discard가 켜져 있으면 §2.3의 "온라인 discard 미사용" 조건이 깨질 수 있었다.

## 5. 실험 순서

**Stage A — age 정의 판정 (선행, 나머지를 무효화할 수 있음).**

    ICAT_ROOT=/home/oy/iCAT FIO_RUNTIME=1800 script/matrix.sh a 3

greedy / cat-create / cat-lastinval × {test2, test3} × 3회 = 18 run. 판정: `LAST_INVAL`이 두 워크로드 모두에서 `CREATE`보다 낮은 WAF를 내면 본문이 옳고 구현이 틀렸던 것이므로 구현을 바꾸고 Stage B를 그 위에서 돌린다. 반대면 본문의 Age 정의와 지역성 논증을 생성 시각 기준으로 다시 쓴다. 동시에 victim 히스토그램으로 age 축의 변별력을 확인한다.

**Stage B — α·강도 ablation (그림 1·2).**

    AGE_MODE=<Stage A 승자> FIO_RUNTIME=1800 script/matrix.sh b 3

α ∈ {5,10,25,50,100,200,400}%, ratio ∈ {4,7,16} × {test2,test3} × 3회 = 60 run. 3회 반복의 표준편차를 반드시 같이 보고해야 §1의 문제가 재발하지 않는다.

**Stage C** — 구간별 WAF 시계열로 워크로드 내부 국면 변화 확인(Ⅳ.1의 주장), 그 다음에야 온라인 튜너 구현.

### 실행 전에 필요한 것 (이 세션에서는 못 함)

- `sudo`가 패스워드를 요구한다. insmod/mkfs/mount가 전부 sudo다.
- `fio`가 설치되어 있지 않다: `sudo apt install fio`. Stage C 이후 SQLite/RocksDB/Filebench arm에는 `sqlite3`, `filebench`, `nvme-cli`도 필요하다.
- 커널 memmap 예약(`memmap=8G$4G`)과 커널 헤더는 이미 갖춰져 있다.
- 시간: run당 preset 포함 약 31분. Stage A ≈ 9.5시간, Stage B ≈ 31시간. 반복 3회를 지키려면 `FIO_RUNTIME`을 줄이는 대신 §1.1의 체류시간 125초를 고려해 최소 900초는 유지하는 편이 좋다.
