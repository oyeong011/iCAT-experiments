# revC-20261124 동시 구동 확인 (고컴, 2026-11-24 14:41–14:45)

본 실험 큐는 보류했다(14:41:26). `queue-order.txt`를 비우고, 사전 등록 순서는 `queue-order.registered.txt`에 보관했다. 단기 실행 4개는 계속 진행한다.

| # | 확인 항목 | 결과 | 근거 |
|---|---|---|---|
| 1 | "승컴·고컴 동시 NVMeVirt 구동 금지"가 명시적으로 대체되었는가 | **아니오.** 11-24 지시("승컴이 E1을 진행하는 동안 고컴이 E2·E6·E7…")는 동시 진행을 뜻하는 것으로 고컴이 해석했을 뿐이다. 금지를 해제한다는 명시적 문장은 없다 | 지시 원문. 이 해석으로 단기 실행 1번째(14:38)를 이미 시작했다 |
| 2 | 물리 SSD, NVMeVirt 장치, 커널 모듈, 마운트 지점이 독립인가 | **고컴 쪽은 독립이다.** | 아래 고컴 사실 |
| | | 고컴 호스트: oy-B550M-DS3H, Ryzen 5 3600XT, 12 스레드 | `hostname`, `nproc` |
| | | 고컴 물리 SSD: nvme0n1 Samsung 970 EVO Plus 1 TB (루트 파일 시스템) | `lsblk` |
| | | 고컴 가상 장치: nvme1n1 CSL_Virt_MN_01 7.5 G, 고컴 RAM의 memmap=8G$4G 예약 영역 | `/proc/cmdline`, `lsblk` |
| | | 고컴 마운트: `/home/oy/iCAT/mnt` ← /dev/nvme1n1 (ext4) | `findmnt` |
| | | 고컴 커널 모듈: 고컴 커널에만 로드된다(nvmev, 사전 등록 해시) | `safety-env.sh` |
| | | 승컴(최신 run 기록): oy-System-Product-Name, i7-7700, RAM 7.6 GiB, 자체 memmap=8G$4G, 자체 CSL_Virt 장치 | 승컴 `validation-600k/…/environment.txt`, `device.txt` |
| 3 | 같은 물리 자원이나 공유 저장장치를 쓰는가 | **쓰지 않는다 (고컴에서 확인 가능한 범위).** | 아래 |
| | | 네트워크 파일 시스템(NFS, CIFS, sshfs, fuse) 마운트: 없음 | `findmnt -t nfs,…` |
| | | 동기화 도구(rsync, syncthing 등) 실행: 없음 | `ps` |
| | | 고컴 ↔ 승컴 ssh 연결: 없음 | `ss` |
| | | 두 장비의 공통점은 GitHub 원격 저장소뿐이다. git push/pull은 측정 경로(가상 장치)와 무관하다 | — |
| | | 승컴 내부 상태(현재 무엇을 실행 중인지)는 고컴에서 직접 볼 수 없다. main의 마지막 승컴 커밋은 14:19 | `git log origin/main` |
| 4 | 실행이 겹칠 때 측정에 영향을 주는 자원 경합 | **장비 사이에는 없다** (CPU·메모리·저장장치가 물리적으로 분리). **고컴 내부에는 경합 요인이 있다:** | 아래 |
| | | 커널 인자에 `isolcpus`가 없다. NVMeVirt 스레드(dispatcher CPU 1, io_worker CPU 2)를 다른 프로세스와 공유할 수 있다 | `/proc/cmdline`, `ps psr` |
| | | 상시 프로세스: chrome-remote-desktop(약 5 % CPU), Xorg, warp-svc, claude, codex app-server(유휴, 0 %) | `ps` (14:41) |
| | | 고컴 분석 작업(예: YCSB 2,012개 파일 스캔, 그림 재생성)을 실행 중에 돌리면 CPU를 쓴다. CAT 점수는 시각(ktime)을 쓰므로, 실행 속도 변화가 GC 선택에 간접 영향을 줄 수 있다(cat47_baseline_audit §2) | — |
| | | revA·revB도 같은 부팅, 같은 상시 프로세스 조건에서 측정했다(isolcpus 없음) | 각 environment.txt |

## 권고 (본 실험 재개 전)

1. 사용자가 동시 구동 허용을 명시적으로 확인한다(항목 1).
2. 본 실험 중에는 고컴에서 무거운 분석(전체 YCSB 스캔, 그림 전체 재생성, check_outputs 전체 모드)을 돌리지 않는다. 가벼운 확인만 한다.
3. 실행마다 부하 기록을 남긴다(예: 30초마다 `/proc/loadavg`와 CPU 1·2 사용률). 경합 여부를 사후에 확인할 수 있게 하려는 것이다. revA의 `memsampler.sh` 방식을 따른다.
4. 재개 방법: `cp -p queue-order.registered.txt queue-order.txt`를 한 뒤, 단기 실행 4개가 모두 exit 0인지 확인하고 `queue.sh`를 다시 실행한다(완료된 run은 건너뛴다).
