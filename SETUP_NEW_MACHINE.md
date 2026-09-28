# 다른 컴퓨터에서 실험 환경 만들기

## 조건
- x86(인텔/AMD) CPU 4코어 이상, **램 16 GB 이상**, Ubuntu 24.04 권장
- **재부팅 가능**해야 함 (램 8 GB를 가상 SSD용으로 예약하는 부팅 설정)
- 사용자 이름 **oy**, 저장소 위치 **/home/oy/iCAT** (스크립트가 이 경로를 씀)

## 순서
```bash
# 0. (다른 이름으로 로그인했다면) oy 사용자 만들기: sudo adduser oy && sudo usermod -aG sudo oy  → oy로 로그인
# 1. 저장소 받기 (비공개 저장소라 GitHub 로그인 필요)
sudo apt-get install -y gh && gh auth login
gh repo clone oyeong011/iCAT-experiments /home/oy/iCAT
# 2. 1단계: 패키지, sudo 권한, 램 예약 → 재부팅
bash /home/oy/iCAT/script/setup-new-machine.sh && sudo reboot
# 3. 2단계: 모듈 70여 개 빌드, YCSB·filebench 설치 (약 20분)
bash /home/oy/iCAT/script/setup-new-machine.sh
# 4. 검증: 이 컴퓨터가 원래 컴퓨터와 같은 값을 내는가 (약 35분)
bash /home/oy/iCAT/script/validate-new-machine.sh
```
검증 결과가 **PASS**(최적 CAT·견고 CAT·Greedy 모두 원래 값과 1% 안)여야 그 컴퓨터의 결과를 원래 결과와 섞어 쓸 수 있다. FAIL이면 그 컴퓨터 결과는 따로 표기한다.

## 주의
- 커널 버전이 다르면 모듈을 그 컴퓨터에서 새로 빌드해야 한다(`script/build-all-modules.sh`가 함). 원래 컴퓨터는 커널 7.0.0-31. 다른 버전에서 빌드가 실패하면 로그(`buildoutput/build-<이름>.log`)를 확인.
- 램이 16 GB면 가상 SSD는 1개만. 32 GB 이상이면 여러 개를 동시에 돌릴 수 있지만 코드 수정(모듈 이름·제어 파일 경로 분리)이 필요하다.
- 가상 SSD가 CPU 1, 2번 코어를 전용으로 쓴다(`script/env.sh`의 `NVMEV_CPUS`).
