# smartgc-src — SmartGC 정책

`varmail-compare-src`(고정 CAT·Greedy)를 복사하고 GC 정책 3번 **SmartGC**를 더한 NVMeVirt 소스다.
출처: Zhao et al., "SmartGC: Enhancing SSD Performance and Lifespan through Intelligent Garbage Collection", IEEE HPCC 2025 (DOI 10.1109/HPCC67675.2025.00022). 원저자 코드는 공개되어 있지 않아 논문 본문만으로 구현했다.

## 무엇을 구현했나

| 논문 | 구현 (`conv_ftl.c`의 `SMARTGC_CORE_BEGIN` ~ `SMARTGC_CORE_END`) |
|---|---|
| 상태 = (이용률, 정규화 erase count), 각 100구간 (Table I) | `smartgc_state()` — 라인(슈퍼블록) 단위. 이 FTL은 라인을 통째로 지운다 |
| 행동 = 블록마다 지움/둠, 희생 블록 목록을 GC에 전달 | `smartgc_step()`이 목록(`smartgc_batch`개)을 만들고 GC는 목록에서만 지운다 |
| 보상 R = w/U + 1/std (Alg. 1) | 지움: `smartgc_on_erase()`, 둠: 1/std |
| Q-learning 갱신 (식 7), ε-greedy (식 8, Alg. 2) | `smartgc_learn()`, `smartgc_step()`, ε는 스텝 수에 따라 반감 |
| GC 버퍼: 예상 erase count 상위 k개 블록을 얼리고 그 블록으로 가는 쓰기를 DRAM에 둠 (III-C) | `smartgc_refreeze()`, `smartgc_absorb()`, `smartgc_drain()`, 읽기는 `smartgc_buffered()` |

스텝 하나 = 희생 목록 하나. 목록을 다 쓰면 새 상태를 관측해 Q를 갱신하고, 얼릴 라인을 다시 정하고, 다음 목록을 고른다.

## 논문이 정하지 않아 직접 정한 것

1. **Q-table은 파티션당 하나**(상태 10,000 × 행동 2). 논문은 블록마다 20 KB라고 적었는데, 여기서는 파티션당 160 MB가 되고 거의 모든 칸이 방문되지 않는다.
2. **"둠" 행동의 보상을 논문과 다르게 줬다.** 논문 Alg. 1은 행동을 가리지 않고 모든 블록에 w/U + 1/std를 준다. 그대로 하면 두 행동의 보상이 같아 구분이 안 되므로, 여기서는 둔 라인에 1/std만 준다. 지운 라인의 다음 상태는 "빈 라인", 둔 라인의 다음 상태는 스텝 끝의 상태다(논문은 둘 다 S_t+1). 지운 라인의 보상에 쓰는 std는 그 라인을 지운 직후의 값이다. U=0인 라인은 유효 페이지 0.5개로 치고, std는 1/16 아래로 내려가지 않게 했다(0으로 나누지 않기 위해).
3. **후보는 무효 페이지가 1개 이상인 닫힌 라인**만. 꽉 찬 라인을 지우면 공간이 생기지 않아 FTL이 멈춘다.
4. **얼린 라인은 목록에 넣지 않는다.** 그래서 III-B의 "금지 블록 벌점"은 적용할 곳이 없고, 정의가 없는 "선호 블록" 규칙은 구현하지 않았다.
5. **얼릴 수 있는 것은 닫힌 라인뿐**(빈 라인·쓰는 중인 라인 제외). 예상 erase count는 E + (직전 스텝 증가분). 상위 k개 안에 든 빈 라인·쓰는 중인 라인은 자리만 차지하므로 실제로 어는 라인은 k개보다 적을 수 있다. 예상값이 같으면 번호가 낮은 라인이 먼저 뽑힌다(논문에 동점 규칙 없음). 그래서 erase count가 모두 0인 실행 초반에는 마모와 무관하게 번호가 낮은 라인이 언다.
6. **GC 버퍼는 모델이다.** NVMeVirt의 FTL은 데이터를 갖고 있지 않으므로 "DRAM에 있다"는 표시만 한다: NAND 기록·무효화 없음. 버퍼에서 읽는 페이지는 NAND 지연 없이 펌웨어 읽기 지연과 PCIe 전송 시간만 든다. 버퍼가 꽉 차면 그 쓰기는 평소처럼 플래시로 간다. 얼림이 풀리면 호스트 페이지 쓰기 1회마다 1페이지씩 플래시에 쓴다(GC 안에서 쓰면 빈 라인이 바닥날 수 있어서). NVMe flush로 비우지 않으며 전원 손실은 고려하지 않는다. 흡수한 페이지의 플래시 사본은 유효로 남으므로 얼린 라인의 이용률은 내려가지 않는다(논문 V-C는 얼린 블록의 이용률이 낮아질 수 있다고 적었다). 풀린 직후의 라인은 버퍼를 비울 때까지 이용률이 높게 보인다.
7. **희생 목록을 Q(s, 지움) 순위로 만든다.** 논문 식 8은 블록마다 지움/둠 중 Q가 큰 행동을 고르고, 본문은 "Q 값이 큰 순서로" 고른다고도 적었다. 여기서는 뒤쪽 읽기를 따라 Q(s, 지움)이 큰 순서로 `smartgc_batch`개(기본 8)를 고른다. 목록 길이는 논문에 없는 파라미터다. Q(s, 둠)은 선택에 쓰지 않고 다음 상태의 최댓값 계산에만 쓰인다. `smartgc_eq8=1`로 식 8을 글자 그대로 읽은 규칙을 고를 수 있다: 후보 라인마다 확률 1−ε로 Q가 큰 행동(동점이면 둠), 확률 ε로 무작위 행동을 고르고, 지움을 고른 라인 전부를 Q(s, 지움)이 큰 순서로 지운다. 이때 `smartgc_batch`는 쓰지 않는다. 지움을 고른 라인이 없으면 무작위 후보 1개를 넣는다(논문에 없는 장치). 동점 규칙과 이 장치도 논문에 없어 직접 정한 것이다. 이 규칙에서는 스텝 하나가 지움 수백~수천 회라서, 스텝 수로 센 ε 반감 주기(기본 2048)가 순위 규칙과 같은 뜻이 아니다. 사용자 공간 구동 비교는 `EXPERIMENT_LOG.md`의 smartgc-eq8-20261119에 있다.
8. **ε-greedy는 식 8을 따른다.** 논문 Alg. 2의 13~17행은 조건이 식 8과 반대로 적혀 있다(ρ < ε이면 최댓값 선택). 코드는 식 8대로 확률 ε로 무작위 선택한다. 논문은 난수를 정규분포로 만든다고 적었지만 여기서는 균등분포다. 무작위 선택은 임의 위치에서 시작해 다음 후보 라인을 고르는 방식이라 완전히 균등하지는 않다.
9. **w, α, γ, ε**는 논문에 값이 없다. 기본값 α=0.5, γ=0.9(논문 Fig. 1 예시 값), w=1, ε 0.3→0.01(2048스텝마다 초과분 반감), GC 버퍼 = 라인의 1%.
10. **Q 초기값** — 아래 참고.

## Q 초기값 (`smartgc_q_init`)

논문은 Q를 0으로 시작한다. 보상이 항상 양수라서, 한 번도 지워 본 적 없는 상태는 지워 본 모든 상태보다 순위가 낮고 ε 탐색으로만 도달한다. 사용자 공간 구동(`test/`, 측정 아님)에서 이 설정은 Greedy보다 WAF가 약 1.8배였고, Q(s, 지움)을 큰 값(2000)으로 시작하면 Greedy와 비슷했다(`EXPERIMENT_LOG.md`의 smartgc-dev-20261114).

- `nvmev-smartgc.ko` — 0에서 시작 (논문 그대로)
- `nvmev-smartgcq.ko` — 2000에서 시작 (빌드 시 `SMARTGC_Q_INIT=2000`)

어느 쪽을 비교 대상으로 쓸지는 정해야 한다. 논문에 실을 때는 어느 쪽인지 밝혀야 한다.

## 빌드와 실행

```bash
bash script/build-all-modules.sh        # nvmev-smartgc.ko, nvmev-smartgcq.ko, nvmev-sg-greedy.ko, nvmev-sg-arm47.ko 포함
bash script/mix-gc-20261010.sh mixY smartgc 1
```

모듈 파라미터(모두 읽기 전용, insmod 때 지정, 단위 ‰): `smartgc_alpha_permille`, `smartgc_gamma_permille`, `smartgc_eps_start_permille`, `smartgc_eps_min_permille`, `smartgc_eps_halflife`(스텝), `smartgc_w_permille`, `smartgc_batch`(1~64), `smartgc_gcbuf_permille`(0 = 버퍼 없음), `smartgc_q_init`, `smartgc_seed`, `smartgc_eq8`(0 = 순위 목록, 1 = 식 8 블록별 선택). Q 계산이 64비트를 넘지 않도록 `smartgc_gamma_permille`은 999, `smartgc_w_permille`과 `smartgc_q_init`은 1,000,000으로 잘린다. 실제 값은 로드할 때 `SmartGC init ...` 줄로 커널 로그에 남는다.

## 계측

`/proc/nvmevirt_measurement`의 기존 줄(첫 줄, `part=` 줄)은 그대로이고 뒤에 줄이 추가된다.

- `wear part=N erase_min= erase_max= erase_mean_milli= erase_std_milli=` — 라인별 erase count. **모든 정책**에서 나오므로 Greedy·CAT의 마모를 보려면 `smartgc-src`로 빌드한 `sg-greedy`, `sg-arm47`을 쓴다(GC 동작은 `varmail-compare-src`와 같음: 사용자 공간 구동에서 host/GC 페이지 수 일치).
- `smartgc part=N steps= explored= eps_permille= absorbed= evicted= gc_flushed= frozen= buf_pages= freezes= thaws= nand_pages= listed=` — `wear` 줄보다 앞에 나온다. `listed`는 희생 목록에 올린 라인 수 누계이고 `listed/steps`가 평균 목록 길이다. `start` 때 0으로 돌아간다(frozen, buf_pages 제외). Q-table도 `start` 때 초기화된다(온라인 학습기와 같은 cold start). 다만 `start` 직전 스텝의 희생 목록은 남아 있어 첫 스텝의 갱신에는 `start` 이전의 전이가 섞인다. `thaws`는 지울 라인이 없어 얼린 라인을 모두 푼 비상 상황의 횟수다.

`smartgc-src` 빌드는 라인 구조체가 커졌고(48 → 72바이트) proc을 읽을 때 마모 통계를 계산한다. GC 선택은 같아도 시간 특성은 `varmail-compare-src` 빌드와 조금 다를 수 있으니, 처리량·지연 비교는 `smartgc-src` 빌드끼리 한다.

**WAF 주의**: `host_pages`는 호스트가 쓴 페이지 수(버퍼가 흡수한 것 포함)이고 `gc_pages`는 GC 복사만 센다. 버퍼에서 플래시로 내보낸 쓰기(`evicted`)는 둘 중 어디에도 없다. 그래서 기존 스크립트의 `1 + gc_pages/host_pages`는 NAND 쓰기 수와 맞지 않는다. 계측 구간에 실제로 NAND에 쓴 페이지 수는 `nand_pages = host_pages − absorbed + evicted + gc_pages`(파티션별)이고, NAND 기준 WAF는 `nand_pages 합 / host_pages`다. `absorbed`와 `evicted`는 `host_pages`처럼 계측 구간에서만 센다. 구간 전체로는 스크립트 값보다 작거나 같지만, 구간 시작 전에 흡수된 페이지가 구간 안에서 나오면 짧은 구간에서는 더 클 수 있다.

모듈을 내릴 때 `Wear: ...`, `SmartGC summary ...` 줄이 커널 로그에 남는다.

## 사용자 공간 구동 (`test/`)

실제 장비에 올리기 전에 FTL 논리를 확인하는 도구다. `conv_ftl.c`, `ssd.c`, `pqueue.c`를 그대로 컴파일하고(커널 API는 `kshim.h`, 채널 모델은 지연 0 스텁) NVMe 쓰기/읽기 명령을 직접 넣으며 매핑·라인·GC 버퍼 불변식을 검사한다. 시간은 가짜 시계이므로 **수치는 측정값이 아니다.**

```bash
bash smartgc-src/test/run.sh smartgc capacity_mib=8192 overwrite_x=6 q_init=2000
SIM_SRC=varmail-compare-src bash smartgc-src/test/run.sh greedy    # 다른 소스 사본을 같은 구동기로
```
