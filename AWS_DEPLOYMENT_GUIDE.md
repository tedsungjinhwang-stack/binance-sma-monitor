# AWS EC2 배포 가이드

바이낸스 SMA 모니터를 AWS EC2에 배포하여 24시간 자동 실행하는 방법입니다.

---

## 📋 목차
1. [AWS 계정 생성](#1-aws-계정-생성)
2. [EC2 인스턴스 생성](#2-ec2-인스턴스-생성)
3. [EC2 접속](#3-ec2-접속)
4. [프로그램 설치 및 설정](#4-프로그램-설치-및-설정)
5. [모니터링 시작](#5-모니터링-시작)
6. [관리 명령어](#6-관리-명령어)

---

## 1. AWS 계정 생성

### 1-1. AWS 회원가입

1. https://aws.amazon.com/ko/ 접속
2. 오른쪽 상단 **"AWS 계정 생성"** 클릭
3. 이메일 주소 입력 후 **"확인 이메일 전송"** 클릭
4. 이메일로 받은 인증 코드 입력
5. 비밀번호 설정 (8자 이상, 대소문자, 숫자, 특수문자 포함)

### 1-2. 연락처 정보 입력

1. **계정 유형**: "개인" 선택
2. 이름, 전화번호, 주소 입력
3. **AWS 고객 계약** 동의 체크
4. **계속** 클릭

### 1-3. 결제 정보 입력

⚠️ **중요**: 무료 티어를 사용해도 신용카드/체크카드 등록은 필수입니다.
- 1년간 무료 티어 사용 가능 (t2.micro, 750시간/월)
- 무료 한도 초과 시에만 과금

1. 카드 정보 입력 (신용카드 또는 체크카드)
2. 청구지 주소 입력
3. **확인 및 계속** 클릭

### 1-4. 본인 확인

1. 전화번호 입력
2. **SMS 전송** 또는 **음성 통화** 선택
3. 받은 인증 코드 4자리 입력

### 1-5. 지원 플랜 선택

1. **기본 지원 - 무료** 선택
2. **가입 완료** 클릭

✅ 계정 생성 완료! (몇 분 후 사용 가능)

---

## 2. EC2 인스턴스 생성

### 2-1. EC2 콘솔 접속

1. https://console.aws.amazon.com/ 로그인
2. 상단 검색창에 **"EC2"** 입력 후 클릭
3. 오른쪽 상단 리전을 **"아시아 태평양(서울) ap-northeast-2"** 로 변경

### 2-2. 인스턴스 시작

1. 왼쪽 메뉴에서 **"인스턴스"** 클릭
2. 오른쪽 상단 **"인스턴스 시작"** 버튼 클릭

### 2-3. 인스턴스 설정

#### 이름 및 태그
- 이름: `binance-sma-monitor` (원하는 이름 입력)

#### 애플리케이션 및 OS 이미지 (Amazon Machine Image)
- **Quick Start**: Ubuntu 선택
- **Amazon Machine Image (AMI)**: **Ubuntu Server 22.04 LTS (HVM), SSD Volume Type** 선택
- **아키텍처**: 64비트 (x86)
- ⚠️ "프리 티어 사용 가능" 표시 확인!

#### 인스턴스 유형
- **t2.micro** 선택 (무료 티어)
- vCPU: 1, 메모리: 1 GiB

#### 키 페어 (로그인)
1. **"새 키 페어 생성"** 클릭
2. 키 페어 이름: `binance-monitor-key` (원하는 이름)
3. 키 페어 유형: **RSA**
4. 프라이빗 키 파일 형식:
   - Windows: **.ppk** (PuTTY 사용 시)
   - Mac/Linux: **.pem**
5. **"키 페어 생성"** 클릭
6. ⚠️ **다운로드된 키 파일 안전하게 보관!** (재발급 불가)

#### 네트워크 설정
- **"기본값 유지"** (자동 할당된 퍼블릭 IP 사용)
- 방화벽 (보안 그룹):
  - ✅ **SSH 트래픽 허용** 체크
  - 소스: **내 IP** 선택 (권장)

#### 스토리지 구성
- **8 GiB gp3** (기본값, 무료 티어 범위)

#### 고급 세부 정보
- **기본값 유지**

### 2-4. 인스턴스 시작

1. 오른쪽 **"요약"** 패널에서 무료 티어 적용 확인
2. **"인스턴스 시작"** 버튼 클릭
3. ✅ "성공적으로 인스턴스를 시작했습니다" 메시지 확인
4. **"인스턴스 보기"** 클릭

### 2-5. 인스턴스 상태 확인

- **인스턴스 상태**: "실행 중" (초록색)
- **상태 검사**: 2/2 통과 (2-3분 소요)

---

## 3. EC2 접속

### 3-1. 퍼블릭 IP 확인

1. EC2 인스턴스 목록에서 방금 만든 인스턴스 선택
2. 하단 **"세부 정보"** 탭에서 **"퍼블릭 IPv4 주소"** 복사
   - 예: `52.79.123.456`

### 3-2. SSH 접속

#### Windows (PowerShell)

1. 다운로드한 `.pem` 또는 `.ppk` 키 파일을 `C:\Users\사용자명\Downloads\` 에 저장
2. PowerShell 열기
3. 키 파일이 있는 폴더로 이동:
   ```powershell
   cd C:\Users\사용자명\Downloads
   ```
4. SSH 접속 (`.pem` 사용 시):
   ```powershell
   ssh -i binance-monitor-key.pem ubuntu@퍼블릭IP주소
   ```
   예:
   ```powershell
   ssh -i binance-monitor-key.pem ubuntu@52.79.123.456
   ```

5. "Are you sure you want to continue connecting?" → `yes` 입력

#### Mac/Linux (Terminal)

1. 다운로드한 `.pem` 키 파일 권한 설정:
   ```bash
   chmod 400 ~/Downloads/binance-monitor-key.pem
   ```
2. SSH 접속:
   ```bash
   ssh -i ~/Downloads/binance-monitor-key.pem ubuntu@퍼블릭IP주소
   ```

✅ 접속 성공 시 `ubuntu@ip-xxx-xxx-xxx-xxx:~$` 프롬프트 표시

---

## 4. 프로그램 설치 및 설정

### 4-1. 자동 설치 스크립트 실행

EC2에 접속한 상태에서:

```bash
# 1. 저장소 클론
cd /home/ubuntu
git clone https://github.com/tedsungjinhwang-stack/binance-sma-monitor.git
cd binance-sma-monitor

# 2. 설정 파일 생성
cp config/config.example.yaml config/config.yaml
```

### 4-2. 설정 파일 수정

```bash
# nano 에디터로 설정 파일 열기
nano config/config.yaml
```

**수정할 부분:**

1. 텔레그램 설정 (61-63번째 줄):
   ```yaml
   TELEGRAM:
     BOT_TOKEN: "여기에_봇_토큰_입력"  # 본인의 텔레그램 봇 토큰
     CHAT_ID: "여기에_채팅ID_입력"     # 본인의 채팅 ID
   ```

2. **Ctrl + O** → Enter (저장)
3. **Ctrl + X** (종료)

### 4-3. 자동 설치 실행

```bash
# 설치 스크립트 실행
bash setup_ec2.sh
```

설치 과정 (약 2-3분):
- ✅ 시스템 업데이트
- ✅ Python 설치
- ✅ 필요한 패키지 설치
- ✅ systemd 서비스 등록

---

## 5. 모니터링 시작

### 5-1. 서비스 시작

```bash
sudo systemctl start sma-monitor
```

### 5-2. 상태 확인

```bash
sudo systemctl status sma-monitor
```

출력 예시:
```
● sma-monitor.service - Binance SMA Monitor
     Loaded: loaded (/etc/systemd/system/sma-monitor.service; enabled; vendor preset: enabled)
     Active: active (running) since ...
```

✅ **Active: active (running)** 표시되면 정상 작동 중!

### 5-3. 실시간 로그 확인

```bash
sudo journalctl -u sma-monitor -f
```

- 로그에서 심볼 스캔, 시그널 발견 등 확인 가능
- 종료: **Ctrl + C**

---

## 6. 관리 명령어

### 서비스 관리

```bash
# 시작
sudo systemctl start sma-monitor

# 중지
sudo systemctl stop sma-monitor

# 재시작
sudo systemctl restart sma-monitor

# 상태 확인
sudo systemctl status sma-monitor

# 자동 시작 활성화 (부팅 시 자동 실행)
sudo systemctl enable sma-monitor

# 자동 시작 비활성화
sudo systemctl disable sma-monitor
```

### 로그 확인

```bash
# 최근 로그 확인
sudo journalctl -u sma-monitor -n 50

# 실시간 로그 (스트리밍)
sudo journalctl -u sma-monitor -f

# 오늘 로그만
sudo journalctl -u sma-monitor --since today
```

### 설정 변경 후 재시작

```bash
# 1. 설정 파일 수정
cd /home/ubuntu/binance_sma_monitor
nano config/config.yaml

# 2. 서비스 재시작
sudo systemctl restart sma-monitor
```

### 코드 업데이트

```bash
# 1. GitHub에서 최신 코드 받기
cd /home/ubuntu/binance_sma_monitor
git pull

# 2. 서비스 재시작
sudo systemctl restart sma-monitor
```

### EC2 인스턴스 중지/시작

**AWS 콘솔에서:**
1. EC2 → 인스턴스 선택
2. **인스턴스 상태** → **인스턴스 중지** (과금 중단)
3. 다시 시작: **인스턴스 시작**

⚠️ 인스턴스 중지 시 퍼블릭 IP가 변경될 수 있음!

---

## 💰 비용 안내

### 무료 티어 (1년간)
- **EC2 t2.micro**: 750시간/월 무료
- **EBS 스토리지**: 30GB/월 무료
- **데이터 전송**: 15GB/월 무료

### ⚠️ 주의사항
- t2.micro 1대만 사용 시 **완전 무료**
- 인스턴스를 중지하면 과금 중단 (스토리지 비용만 소량 발생)
- 1년 후 유료 전환 시: 월 $10 내외

### 비용 모니터링
1. AWS 콘솔 → 우측 상단 계정명 클릭
2. **결제 대시보드** → 현재 사용량 확인

---

## 🔧 문제 해결

### 접속이 안 될 때
```bash
# 보안 그룹 확인 (AWS 콘솔)
EC2 → 인스턴스 → 보안 탭 → 보안 그룹 → 인바운드 규칙
→ SSH (22번 포트) 허용 확인
```

### 서비스가 시작 안 될 때
```bash
# 에러 로그 확인
sudo journalctl -u sma-monitor -n 100 --no-pager

# 설정 파일 확인
cat config/config.yaml
```

### 텔레그램 알림이 안 올 때
```bash
# 설정 확인
grep -A 2 "TELEGRAM:" config/config.yaml

# 테스트 실행
cd /home/ubuntu/binance_sma_monitor
python3 test_telegram.py
```

---

## ✅ 완료!

이제 바이낸스 SMA 모니터가 AWS EC2에서 24시간 자동으로 실행됩니다.

- 15분마다 자동 스캔
- 조건 충족 시 텔레그램 알림
- 서버 재부팅 시 자동 재시작

---

## 📞 지원

문제가 있을 경우:
1. 로그 확인: `sudo journalctl -u sma-monitor -f`
2. GitHub Issues: https://github.com/tedsungjinhwang-stack/binance-sma-monitor/issues
