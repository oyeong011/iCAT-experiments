# M7 환경 일반화: 검증된 범위와 한계 (Discussion용, 고컴 2026-11-25)

- 새 환경 실험은 하지 않았다. 아래 값은 실행 모듈의 소스(`revC-src/ssd_config.h`, `Kbuild`)와 러너 insmod 인자, 각 run의 `environment.txt`에서 읽었다.

## 1. 실험 환경 (모든 iCAT 결과에 공통)

| 항목 | 값 | 출처 |
|---|---|---|
| SSD | NVMeVirt 에뮬레이터 (실물 SSD가 아님), `BASE_SSD=SAMSUNG_970PRO` 설정, conventional FTL (페이지 매핑) | `Kbuild:21`, `ssd_config.h:63–107` |
| NAND 구성 | MLC, 채널 8 × LUN 2 × plane 1. flash page 32 KiB, 파티션당 line(슈퍼블록) 8,192개 | `ssd_config.h:71–80` |
| 지연 모델 | 읽기 36 µs ± 6 µs, 프로그램 185 µs, **erase 0 ns**. 채널 800 MB/s, PCIe 3,360 MB/s | `ssd_config.h:85–96` |
| 용량 | 에뮬레이션 메모리 8 GiB (`memmap_start=4G memmap_size=8192M`). FTL 파티션 4개 | 러너 insmod 인자 |
| OP | 7 % (`OP_AREA_PERCENT 0.07`) | `ssd_config.h:103` |
| GC 시작 | 빈 line 2개 이하 (`gc_thres_lines = 2`) | `conv_ftl.c:1182` |
| 파일 시스템 | ext4, nodiscard (TRIM 없음) | 러너 |
| 초기 상태 | Table-3 준비: 6 GiB 순차 + 3 GiB 4k 랜덤 쓰기 (seed 20260907) | 러너 |
| 호스트 | 고컴 Ryzen 5 3600XT (6코어 12스레드), 승컴 i7-7700. 둘 다 커널 7.0.0-31 | `environment.txt` |
| 에뮬레이터 스레드 | 전용 CPU 1, 2 (busy-poll) | 러너, loadsampler (고컴 revC는 CPU 1·2 99.8–100 % 확인) |

## 2. 검증된 워크로드 범위 (유효 데이터만)

| 종류 | 워크로드 | 반복 | 비고 |
|---|---|---|---|
| 합성 쓰기 | FIO test4 (FIO-Fast), test3 (FIO-Slow) 단일 10 h, 60조합 sweep | n=1 (sweep), 일부 n=3 | YCSB 없음 |
| 응용 | Varmail, Webserver, Webproxy, Videoserver, OLTP (Filebench), SQLite YCSB-A 단일 | n=1–3 | 단일 부하 |
| 전환 | mixC, D, F, K, O, P 등 8종 (13종 중), mixY 20단계 10 h, **mixFYF (FIO-Fast → YCSB-A 250k → FIO-Fast)** | mixFYF는 정책별 n=3, 나머지는 n=1–3 | YCSB가 들어간 9월 전환 5종과 11-23 E1은 무효 (`paper_data_validity_matrix.md`) |
| 통계 검정이 가능한 묶음 | 고컴 mixFYF (revA, revB, revC), 승컴 mixFYF (revD, abl, greedy) | 각 n=3 | 호스트 사이는 합치지 않는다 |

## 3. 검증하지 않은 것 (논문에서 주장하지 않을 것)

| 차원 | 실험한 값 | 하지 않은 것 | 일반화할 때의 위험 |
|---|---|---|---|
| SSD 종류 | 에뮬레이터 1종 (970PRO 설정, MLC) | 실물 SSD, TLC/QLC, ZNS, 다른 FTL(하이브리드 매핑) | 지연, 병렬성, GC 비용 모델이 다르면 arm별 WAF 순위가 바뀔 수 있다. iCAT은 WAF를 직접 관측해 고르므로 원리상 적응하지만 **측정하지 않았다** |
| erase 지연 | 0 | 실제 erase 시간(수 ms) | GC 비용이 쓰기 증폭에만 반영되고 시간 지연에는 거의 반영되지 않는다. 지연과 처리량 결과를 실물 SSD로 옮길 수 없다 |
| 용량 | 8 GiB (파티션 4개) | 수백 GB–TB | 판단 구간(512 MiB, GC 128회)은 고정 크기다. 용량이 커지면 한 구간의 의미와 수렴 시간이 달라진다. 학습 메모리(10 KB)는 용량과 무관하다 |
| OP 비율 | 7 % | 다른 OP (예: 28 %) | OP가 커지면 GC 압력과 정책 간 WAF 차이가 줄어들 수 있다 |
| 부하 강도 | FIO `rate_iops` 고정 (hot 24k / warm 12k / cold 4k), YCSB는 시간 기준 | 다른 강도와 큐 깊이 | 고컴과 승컴에서 같은 1,800 s 동안 YCSB 처리량이 달랐다 (약 1.5억 대 1.1억 요청). 같은 부하 이름이라도 쓰기량이 호스트마다 다르다 |
| 실행 시간 | 90분 (mixFYF), 10 h (mixY, 단일) | 수일–수주 | 할인 γ의 반감기는 약 1,376 구간이다. 90분 실험에서는 할인이 거의 작동하지 않는다 [계산] |
| TRIM | 없음 (nodiscard) | discard 사용 | 무효 페이지 분포가 달라진다 |
| 반복 | n=3 (mixFYF), n=1 (mixY, SmartGC, 10 h 단일) | n ≥ 5, 다른 seed 계열 | n=3이라 df ≈ 2–4, 검정력이 낮다 |
| 호스트 | 2대 (Ryzen, i7) | — | 같은 부하라도 호스트에 따라 V4 절대값이 다르다 (고컴 revA-v4 2.128 대 승컴 revD-v4). 그래서 비교는 항상 같은 호스트, 같은 배치 안에서 했다 |

## 4. Discussion 문단 초안

> All results come from one emulated SSD configuration: NVMeVirt, conventional page-mapping FTL, MLC timing, 8 GiB, 7 % over-provisioning, four FTL partitions, and zero erase latency. Workloads were FIO, Filebench, and SQLite/YCSB on ext4 without discard. Statistical comparisons use n = 3 runs per policy within the same host and batch.
>
> We did not evaluate real SSDs, other capacities or over-provisioning ratios, TLC/QLC timing, or runs longer than 10 hours. iCAT chooses CAT parameters from observed WAF and does not depend on a device model. We therefore expect it to adapt to such changes. However, the ranking of fixed CAT settings and the size of iCAT's gains may differ, and we have not measured this.
>
> The decision window is fixed at 128 GCs and 512 MiB of host writes. It should scale with device capacity. We leave this, and validation on real hardware, to future work.

**한국어 요지**
- 결과는 에뮬레이터 한 가지 구성(8 GiB, OP 7 %, MLC, erase 0)에서 얻었다.
- 실물 SSD, 다른 용량과 OP, 장시간 운용으로 일반화하는 것은 측정하지 않은 가설이다.
