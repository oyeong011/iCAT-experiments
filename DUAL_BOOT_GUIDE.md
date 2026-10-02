# 새 컴퓨터: 윈도우 + Ubuntu 듀얼 부팅부터 실험 준비까지

설치 파일: **ubuntu-24.04.4.1-desktop-amd64.iso** (ubuntu.com). 사용자 이름은 반드시 **oy**.

## 0. 이미 끝낸 것
- [x] Rufus로 USB 굽기 (GPT / UEFI / ISO 이미지 모드)
- [x] 디스크 관리에서 C: 축소 → "할당되지 않음 150 GB" (그대로 둘 것)

## 1. 윈도우에서 두 가지 끄기
- [ ] **BitLocker / 장치 암호화**: 시작 메뉴 "BitLocker 관리" 검색 → 켜져 있으면 "끄기" → 해제 완료까지 대기. (Home 버전: 설정 → 개인 정보 및 보안 → 장치 암호화 → 끔)
- [ ] **빠른 시작**: 제어판 → 하드웨어 및 소리 → 전원 옵션 → 전원 단추 작동 설정 → "현재 사용할 수 없는 설정 변경" → "빠른 시작 켜기" 체크 해제 → 저장

## 2. BIOS에서 Secure Boot 끄기
- [ ] 설정 → 시스템 → 복구 → 고급 시작 옵션 "지금 다시 시작"
- [ ] 문제 해결 → 고급 옵션 → **UEFI 펌웨어 설정** → 다시 시작
- [ ] Boot 또는 Security 탭 → **Secure Boot → Disabled** (ASUS: Advanced Mode(F7) → Boot → Secure Boot → OS Type을 "Other OS")
- [ ] F10 → 저장 후 나가기

> 이걸 빠뜨리면 나중에 가상 SSD 모듈이 "Key was rejected by service"로 거부된다.

## 3. USB로 부팅
- [ ] USB를 꽂은 채 켜면서 **F12** 연타 (안 되면 F11 / F8 / ESC / F2 부팅 메뉴)
- [ ] **UEFI: (USB 이름)** 선택 → "Try or Install Ubuntu"
- [ ] 화면이 안 나오거나 멈추면: Rufus로 USB를 **DD 이미지 모드**로 다시 굽고 재시도

## 4. Ubuntu 설치
- [ ] 언어 **한국어** → 접근성 다음 → 키보드 **한국어** → **인터넷 연결** (가능하면 유선)
- [ ] "Ubuntu 설치" → **대화형 설치** → **기본 선택** → 추가 소프트웨어(그래픽·Wi-Fi 드라이버, 미디어 코덱) 둘 다 체크
- [ ] ⚠️ 설치 방식: **"Windows Boot Manager와 함께 Ubuntu 설치"**
  - **"디스크를 지우고 Ubuntu 설치"는 절대 고르지 말 것** (윈도우가 지워짐)
  - 이 선택지가 없으면 진행하지 말고 화면의 선택지를 확인할 것 (BitLocker가 켜져 있거나 빈 공간이 안 보이는 경우)
- [ ] 계정: 이름 아무거나 / **사용자 이름 `oy`** / 컴퓨터 이름 예: `icat-2` / 비밀번호
- [ ] 시간대 **Seoul** → 설치 → "지금 다시 시작" → USB 빼고 Enter

## 5. 설치 확인
- [ ] 켤 때 메뉴에 **Ubuntu / Windows Boot Manager**가 나오면 성공
- [ ] 메뉴 없이 윈도우로 켜지면: BIOS → Boot 순서에서 **ubuntu**를 맨 위로
- [ ] (선택) 윈도우 시계가 틀어지면 Ubuntu 터미널에서 `timedatectl set-local-rtc 1`

## 6. 실험 환경 설치 (Ubuntu 터미널: Ctrl + Alt + T)

```bash
# 6-1. 기본 확인 (결과를 기록해 둘 것)
free -g | head -2; nproc; lscpu | grep 'Model name'; uname -r
#   메모리 total이 15 이상이어야 함 (16 GB 이상)

# 6-2. 커널을 기존 실험 컴퓨터와 같은 7.0.0-31로 (uname -r이 7.0.0-31-generic이면 건너뜀)
sudo apt update
sudo apt install -y linux-image-7.0.0-31-generic linux-headers-7.0.0-31-generic linux-modules-extra-7.0.0-31-generic
#   설치 후 재부팅, 켤 때 Ubuntu 메뉴 → "Advanced options for Ubuntu" → 7.0.0-31 선택
#   (기본 부팅으로 고정하려면 원격 접속 후 설정)

# 6-3. 저장소 받기 (GitHub 로그인: 화면 안내대로 브라우저에서 코드 입력)
sudo apt install -y gh git && gh auth login
gh repo clone oyeong011/iCAT-experiments ~/iCAT

# 6-4. 1차 설정: 패키지, sudo 권한, 메모리 8 GiB 예약 → 재부팅
bash ~/iCAT/script/setup-new-machine.sh && sudo reboot

# 6-5. 재부팅 후 2차 설정: 가상 SSD 모듈 빌드, YCSB·Filebench 설치 (약 20분)
bash ~/iCAT/script/setup-new-machine.sh

# 6-6. 검증: 기존 컴퓨터와 같은 값이 나오는지 (약 35분) → 마지막 줄 PASS / FAIL
bash ~/iCAT/script/validate-new-machine.sh
```

## 7. 원격 접속을 열어 둘 경우 (선택)
```bash
sudo apt install -y openssh-server
mkdir -p ~/.ssh && echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIWecGriuXg/XzlVjaNbMtjc6H5h1EBBaGgHUZeaJ2jH oy@oy-System-Product-Name" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
hostname -I
```
기존 실험 컴퓨터와 같은 공유기에 연결되어 있으면, IP 주소를 알려 주면 6단계 이후를 원격으로 진행할 수 있다.

## 막혔을 때 알려 줄 것
- 화면에 보이는 글자 그대로 (사진도 가능)
- 6단계에서 실패하면 마지막 20줄: `... 2>&1 | tail -20`
