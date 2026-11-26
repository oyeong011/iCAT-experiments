# cpu_check=unavailable 원인 조사 (2026-11-26 20:30, 실행 중인 큐는 건드리지 않음)

## 결론
- `cpu_check=unavailable (FileNotFoundError)`은 **CPU 계측 실패**이고, CPU 계측 성공이 아니다.
- batchG의 smoke 3개와 본 실험 전체에서 NVMeVirt CPU 사용률을 **측정하지 않았다.**
- 승컴의 revD-20261124, revision-additional-ablation, greedy-20261125 checks.tsv도 모든 줄이 같은 값이다. 즉 승컴 배치 전체에 해당한다.

## 원인
- `check-run.py` 36–48행은 `result/batchG-20261126/loadsampler.tsv`를 읽는다. 이 파일은 30초마다 /proc/stat에서 cpu1·cpu2 busy %를 기록한다.
- 이 파일을 만드는 `loadsampler.sh`는 **고컴 캠페인 구성요소**다. 처음 나타난 곳은 revC-20261124 (커밋 6775819da)이다.
- 승컴 러너와 queue.sh는 이 샘플러를 띄우지 않는다. 그래서 파일이 없고 FileNotFoundError가 난다.
- 체크 코드를 고컴에서 그대로 옮겨 오면서 샘플러는 함께 옮겨지지 않았다.

## 조치
- **실행 중인 배치에 샘플러를 추가하지 않는다.** 일부 run만 측정되면 배치 안에서 조건이 달라지기 때문이다.
- 지난 run의 CPU 사용률은 사후에 복원할 수 없다 (/proc/stat 누적값을 남기지 않았다).
- 이 검사가 원래 보는 것은 "NVMeVirt 디스패처 코어(cpu1·cpu2)가 95 % 이상 바쁜가"이다. 시뮬레이터 상태를 확인하는 장치다.
  - 정책별 CPU 오버헤드 지표가 아니다. 두 코어는 정책과 상관없이 busy-poll한다.
- **정책 오버헤드는 사전 등록대로 다음으로만 보고한다.**
  - `learner_ns`: 커널 ktime으로 잰 학습기 경과 시간이다. CPU 시간은 아니다. V4와 drift50에만 있다.
  - 자료구조 크기 (계산값)
- **CPU 오버헤드는 "측정하지 않음"으로 명시한다.**
- 다음 배치부터 CPU를 재려면 큐 시작 전에 loadsampler.sh를 승컴 경로로 옮겨 띄워야 한다. 승인이 필요하다.
