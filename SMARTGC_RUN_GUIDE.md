# SmartGC 실험 컴퓨터 실행 순서

실험 컴퓨터(`/home/oy/iCAT`)에서 `smartgc-src` 모듈을 빌드하고 돌리는 명령을 순서대로 적었다. 구현 설명은 `smartgc-src/SMARTGC.md`, 검증 절차는 `.claude/skills/verify-nvmevirt-gc/`에 있다.

**주의**: 이 모듈은 실제 커널에 올려 본 적이 없다(2026-11-19 기준). 3번의 짧은 실행이 첫 실제 시험이고, 그 명령 조합(`SMOKE=1` + `t4`)도 돌려 본 적이 없다. 실험 컴퓨터가 아닌 곳에서는 `CODEX_HANDOFF.md`를 먼저 읽는다.

## 1. 받기와 상태 확인

```bash
cd /home/oy/iCAT && git pull
bash .claude/skills/verify-nvmevirt-gc/verify.sh doctor
```

`nvmev not loaded`가 나오고 `device.lock is HELD`가 없어야 한다. 다른 실험이 돌고 있으면 여기서 멈춘다.

## 2. SmartGC 모듈 6개만 빌드

```bash
K=/lib/modules/$(uname -r)/build
b() { tag=$1; shift
  make -C "$K" M="$PWD/smartgc-src" clean >/dev/null 2>&1
  make -C "$K" M="$PWD/smartgc-src" -j"$(nproc)" "$@" modules > "buildoutput/build-$tag.log" 2>&1 \
    && install -m0644 smartgc-src/nvmev.ko "buildoutput/nvmev-$tag.ko" \
    && echo "built $tag $(sha256sum < "buildoutput/nvmev-$tag.ko" | cut -c1-64)" \
    || echo "BUILD FAIL $tag (buildoutput/build-$tag.log)"; }
b smartgc   NVMEVIRT_GC_POLICY=SMARTGC
b smartgcq  NVMEVIRT_GC_POLICY=SMARTGC SMARTGC_Q_INIT=2000
b smartgc-eq8  NVMEVIRT_GC_POLICY=SMARTGC SMARTGC_EQ8=1
b smartgcq-eq8 NVMEVIRT_GC_POLICY=SMARTGC SMARTGC_EQ8=1 SMARTGC_Q_INIT=2000
b sg-greedy NVMEVIRT_GC_POLICY=GREEDY
b sg-arm47  NVMEVIRT_GC_POLICY=CAT_FIG7 FIXED_ARM=47
```

`bash script/build-all-modules.sh`로도 되지만, 그쪽은 기존 모듈 70여 개를 전부 다시 빌드해 덮어쓰고 매니페스트를 새로 쓴다(약 15분). 출력된 SHA256은 `EXPERIMENT_LOG.md`에 적는다.

| 모듈 | 내용 |
|---|---|
| `nvmev-smartgc.ko` | SmartGC, Q-table을 0에서 시작(논문 그대로) |
| `nvmev-smartgcq.ko` | SmartGC, Q(s, 지움)을 2000에서 시작 |
| `nvmev-smartgc-eq8.ko` | SmartGC, 식 8 블록별 선택 규칙, Q 0 시작 |
| `nvmev-smartgcq-eq8.ko` | SmartGC, 식 8 블록별 선택 규칙, Q 2000 시작 |
| `nvmev-sg-greedy.ko` | Greedy + 마모 통계 줄 |
| `nvmev-sg-arm47.ko` | 고정 CAT arm47 + 마모 통계 줄 |

## 3. 짧은 실행으로 로드 확인

```bash
env SMOKE=1 bash script/mix-gc-20261010.sh t4 smartgc 1
d=result/gc-20261010/t4-smartgc-rep1-smoke
cat $d/final-control.txt
grep -c "SmartGC init" $d/kernel.log
grep -i "BUG\|Oops\|Call Trace\|soft lockup" $d/kernel.log
lsmod | grep nvmev
```

정상이면 다음과 같다.

- `final-control.txt` 첫 줄의 `host_pages`와 `gc_pages`가 0보다 크다.
- `smartgc part=` 줄 4개와 `wear part=` 줄 4개가 있고, `steps`가 0보다 크다.
- `SmartGC init` 개수가 4다.
- 마지막 두 명령은 아무것도 출력하지 않는다.

스크립트가 실험일지 항목을 스스로 추가한다. 실패하면 로그를 지우지 말고 일지에 실패로 적는다.

## 4. 본 실험

mixY 한 번은 20구간 × 1800초로 약 10시간이다.

```bash
SEQ="F S V F V S F S V F V S F S V F V S F S"
env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY smartgc 1
env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY smartgcq 1
env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY sg-greedy 1
env MIXY_SEQ="$SEQ" PH_SECS=1800 bash script/mix-gc-20261010.sh mixY sg-arm47 1
```

- 식 8 선택 규칙으로 돌리려면 정책 이름을 `smartgc-eq8`(Q 0) 또는 `smartgcq-eq8`(Q 2000)로 바꾼다. 결과 디렉터리 이름에 정책 이름이 들어가므로 설정이 섞이지 않는다.
- `smartgc`, `smartgcq`, `smartgc-eq8`, `smartgcq-eq8` 중 어느 쪽을 비교 대상으로 쓸지는 아직 정해지지 않았다. 결과를 적을 때 어느 쪽인지 밝힌다.
- `sg-greedy`와 `sg-arm47`은 마모 통계가 필요하거나 처리량·지연을 SmartGC와 같은 조건으로 비교할 때만 돌린다. WAF만 볼 거면 기존 Greedy·arm47 결과를 써도 된다.
- 결과 디렉터리가 이미 있으면 스크립트가 덮어쓰지 않고 멈춘다.
- 한 번에 하나만 돌 수 있다(`device.lock`).

## 5. SmartGC의 NAND 기준 WAF

스크립트가 계산하는 WAF는 `1 + gc_pages/host_pages`라서 GC 버퍼 효과가 빠져 있다. 실제 NAND 쓰기 기준 값은 이렇게 구한다.

```bash
awk '/^smartgc part=/{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="nand_pages")n+=a[2]}}
     NR==1{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="host_pages")h=a[2]}}
     END{printf "WAF_nand=%.6f\n", n/h}' result/gc-20261010/mixY-smartgc-rep1/final-control.txt
```

경로의 `mixY-smartgc-rep1`은 스크립트 규칙에서 읽은 디렉터리 이름이다. 실제로 생긴 이름을 확인하고 쓴다.
