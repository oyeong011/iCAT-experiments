# 측정 방법 (resource-v124-20261114)

## 대상과 조건
- 정책 4개: Fixed CAT-47(arm 47 = k 10, scale 25%, ratio 16, 학습기 컴파일 제외), iCAT v1, v2, v4(구현 그대로; `implementation_audit.md` 참조).
- 같은 PC(i7-7700 4C/8T, RAM 7.6 GiB, Ubuntu 24.04, 커널 7.0.0-31, gcc 13.3.0), 같은 insmod 인자(`memmap_start=4G memmap_size=8192M cpus=1,2 measurement_manual=1`), 같은 SSD 구성(RAM 기반 8 GiB, FTL 파티션 4개, 파티션당 line 8,192개), 같은 컴파일 옵션(학습 정책 선택과 `-DRES_INSTR`, Fixed는 `-DCONV_FIXED_ARM=47`만 다름).
- 초기 상태: 매 실행마다 모듈 새로 적재(빈 SSD) → mkfs.ext4 → mixY 준비(6 GiB 파일 128 KiB 순차 쓰기 + 3 GiB 4 KiB 무작위 쓰기, seed 고정) → `drop_caches` 후 측정 시작.
- 부하: FIO-Fast(`workloads/mix-test4.fio`, 핫:웜:콜드 = 6:3:1) 1,800초.
- 반복과 순서: 정책당 3회, 회차마다 순서를 바꿈(1회 F/v1/v2/v4, 2회 v4/v2/v1/F, 3회 v2/F/v4/v1). 이어서 계측 없는 모듈로 정책당 1회(WAF 영향 확인).

## 측정 구간
`/proc/nvmevirt_measurement`에 `start`를 쓴 시점(준비가 끝난 직후, `started.txt`)부터 `stop`을 쓴 시점(`stopped.txt`)까지. 학습기와 계측 카운터는 이 구간(`conv_measure_active`)에서만 동작한다. kthread CPU와 메모리는 이 두 시점에 가장 가까운 10초 간격 표본의 차이로 계산한다.

## CPU
- 학습은 별도 스레드가 아니라 `nvmev_dispatcher` 커널 스레드가 GC 안에서 동기적으로 실행한다(`do_gc` → `watgc_v2_on_gc`). 지시서의 `clock_gettime()`/`CLOCK_THREAD_CPUTIME_ID`는 사용자 공간 API라 커널 모듈에 쓸 수 없다. 대신 커널의 `ktime_get_ns()`(CLOCK_MONOTONIC과 같은 시계)로 구간 시간을 잰다.
- 이 구간 시간을 CPU 시간으로 봐도 되는 근거: dispatcher는 CPU 1에 고정된 바쁜 대기 스레드이고, `/proc/PID/schedstat`의 실행 시간(스레드 CPU 시간과 같은 값)이 측정 구간 경과 시간의 약 99.9%였다(=거의 선점되지 않음). 이 비율은 매 실행 `cpu_overhead_summary.csv`에 기록한다.
- 카운터(파티션별 호출 수·합·최대): `dogc`(GC 1회 전체, 학습 포함), `ongc`(학습 진입 1회 전체), `observe`(정책 결정 1회 = 보상 갱신 + 정책 선택), `update`(보상 갱신: drift 검사, 할인, 표본 추가, 최선 갱신, v4 후보 제거), `select`(정책 선택), `log`(결정마다 남기는 printk), `setarm`(새 조합 적용).
- 학습 CPU = `ongc` 합. 공통 GC 비용 = `dogc` − `ongc`. Fixed CAT의 `ongc`는 빈 함수 호출과 시계 2회 읽기의 비용이므로 계측 자체의 비용으로 따로 보고하고 학습 CPU는 0으로 둔다.
- 지시서 8절의 CPU 추가 비용(%)은 기준(Fixed) 학습 CPU가 0이라 정의할 수 없어 계산하지 않는다. 대신 학습/dispatcher CPU(%)와 학습/공통 GC 비용(%)을 보고한다. dispatcher 전체 CPU 기준 백분율은 계산은 하되, 바쁜 대기 때문에 ~100%로 포화되어 학습 비용을 반영하지 못함을 명시한다.
- perf는 sudo가 필요해 쓰지 않았다(지시서 5절).

## 메모리
- 자료구조: 빌드된 각 `.ko`의 DWARF 정보에서 gdb `ptype /o`로 구조체 크기와 멤버별 크기를 읽는다(`data_structure_sizes.csv`). 실행 시에도 모듈이 `sizeof` 값을 `RESOURCE` 줄로 출력해 일치를 확인한다. 학습 코어에는 동적 할당이 없다.
- 실행 메모리: `/proc/meminfo`의 VmallocUsed, Slab, SUnreclaim, Percpu, KernelStack을 적재 전·후·실행 중(10초 간격)·제거 후에 기록하고, `/sys/module/nvmev/coresize`를 기록한다.
- 지시서의 `/proc/PID/status`(VmRSS, VmHWM)와 `smaps_rollup`(PSS)은 NVMeVirt kthread에 없다(커널 스레드는 주소 공간 mm이 없음). 매 표본에서 확인한 결과를 "N/A (kthread, no mm)"로 기록한다. 8 GiB 에뮬레이션 저장 공간은 부팅 시 예약된 memmap 영역이라 어떤 할당자 통계에도 잡히지 않는다.
- 공통 메모리와 학습 메모리를 실측으로 분리할 수 없는 이유: 고정 CAT 빌드도 같은 `struct conv_ftl`(튜너 포함)을 할당하므로 두 빌드의 할당량은 같다. 학습 전용 바이트는 자료구조 분석값으로 보고하고, VmallocUsed 실행 중 변동(표준편차)을 측정 해상도로 함께 적는다.

## 계측의 영향
- `RES_INSTR` 없이 빌드한 복사본의 `.text`는 원본 모듈과 sha256이 같다(계측 외 변경 없음).
- 계측 빌드 3회 WAF와 비계측 1회 WAF를 비교한다(`resource_summary.csv`).
- 시계 비용은 Fixed CAT의 `ongc`(빈 호출 + `ktime_get_ns` 2회)로 GC 1회당 값을 보고한다.

## Smart GC
원문 구현 없음(이 PC, 저장소 main/icat-2, Obsidian vault 확인). 논문(Zhao et al., IEEE HPCC 2025, DOI 10.1109/HPCC67675.2025.00022)은 비공개이고, 공개 초록(OpenAlex)에는 "강화학습 에이전트가 SSD 내부 상태를 보고 GC 희생 블록을 고른다"는 내용만 있다. 블록별 Q-table, 상태 수, 항목 크기는 초록에 없다. 따라서 Smart GC는 실행 측정과 Q-table 크기 모두 미측정이며, `smartgc_theoretical_estimate.csv`에는 장치 기하(블록 수)와 초안 숫자의 역산만 적는다.
