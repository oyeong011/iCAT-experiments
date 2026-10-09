# 명시적 WAF 측정

기본 모드는 기존 첫-GC 이후 계측을 유지한다. 새 모드는 모듈 로드 시 `measurement_manual=1 measurement_uid=1000`으로 켠다. 정책이나 SSD 배치는 바꾸지 않고, 통계의 시작과 끝만 정한다. UID는 실제 실험 사용자에 맞추며 기본은 root이다.

## 사용 순서

1. 실험일지에 모듈 hash, 정책, 준비 작업, 측정 입력과 실행량을 기록한다.
2. 새 장치에 정해진 준비 작업을 수행한다. fio 완료와 flush/sync 완료를 확인한다.
3. `/proc/nvmevirt_measurement`에 `start`를 쓴다. 전체 FTL 통계가 함께 0으로 초기화되고 새 epoch가 시작된다. 데이터, mapping, Age, write pointer는 초기화하지 않는다.
4. 정해진 입력량을 실행하고 fio 완료 및 flush/sync를 확인한다.
5. 같은 제어 파일에 `stop`을 쓴 뒤 읽어 최종 결과를 저장한다. 이후 쓰기와 unmount는 해당 결과를 바꾸지 않는다.
6. 새 `start`는 이전 결과를 지우므로 반드시 먼저 파일에 보존한다.

```sh
printf 'start\n' > /proc/nvmevirt_measurement
# 정해진 measured workload 실행 및 flush/sync
printf 'stop\n' > /proc/nvmevirt_measurement
cat /proc/nvmevirt_measurement
```

시작/종료는 FTL의 전체 NVMe 명령 처리와 같은 mutex로 직렬화된다. 명령을 처리하는 중간에 카운터를 reset하지 않는다. 이것은 장치 queue를 비우는 기능이 아니므로 준비 작업과 측정 작업을 겹쳐 실행하지 않는다.

## 출력과 해석

- `epoch`: start 횟수, `active`: 현재 계측 여부.
- `host_bytes`: 성공적으로 받아들인 NVMe write 명령의 정확한 요청 바이트 수. FTL 처리에서 재시도된 요청을 중복 계산하지 않는다.
- `host_pages`: 새로 할당한 host FTL 페이지 수.
- `gc_pages`: GC relocation에 할당한 FTL 페이지 수.
- 각 `part` 줄: partition별 host/GC 페이지 수와 GC 횟수.
- 페이지 기반 WAF: `(host_pages + gc_pages) / host_pages`. host_pages=0이면 정의하지 않는다.

검증은 4 KiB 정렬 쓰기로 수행했다. 부분 페이지 요청에서는 host_pages×4096과 host_bytes가 다를 수 있으므로 혼동하지 않는다. `gc_pages`는 독립적으로 관측한 물리 NAND program bytes가 아니다.

중복 start는 EBUSY, 이미 정지한 상태의 stop과 잘못된 명령은 EINVAL로 거부한다. 제어 파일은 지정 UID만 접근할 수 있는 0600이다. 초기화 실패 이후 남는 endpoint가 없도록 최종 초기화 단계에서 만들고, namespace 메모리를 해제하기 전에 제거한다.

최종 결과는 stop 후 읽는다. active 상태에서 작은 read를 여러 번 하면 서로 다른 시점의 snapshot이 이어질 수 있다. 기존 window 로그는 페이지 경계 방식이며, 이번 구현이 window별 reward의 인과 귀속까지 검증한 것은 아니다.

## 검증 실행기

`script/verify-measurement-20260907.sh <module-tag> [new-run-label]`은 새 가상 SSD만 대상으로 계측 정확성을 확인한다. 기존 NVMe 장치나 mount가 있으면 중단한다. 실행마다 장치를 새로 만들고 해제하므로 성능 비교용 workload와 구분한다.

- 6 GiB sequential preset + 3 GiB random preparation 후 통계 0 확인.
- 1 GiB random write의 요청 바이트 수를 Linux block-stat sectors와 대조. 파일시스템 metadata 쓰기도 둘에 포함된다.
- 모든 partition 합계 및 GC copy 양수 확인.
- stop 후 256 MiB 추가 쓰기에도 snapshot 불변 확인.
- 재start/reset 후 stop하고 1 MiB 데이터 표본 checksum이 보존되는지 확인.
- 새 epoch에서 128 MiB 쓰기의 요청 바이트 수를 다시 대조.
- start/stop 경계 전후 block stats가 같아 추가 쓰기가 끼지 않았는지 확인. 조용하지 않은 경계는 실패로 기록하고 결과를 승인하지 않는다.

실패 기록도 보존한다. 이 검증만으로 독립 NAND 계측, 장시간 동시 제어 스트레스, 정책 간 동일 SSD 내부 배치, iCAT 학습 효과가 검증된 것은 아니다.
