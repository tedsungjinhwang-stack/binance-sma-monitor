# 바이낸스 SMA 모니터 프로젝트 정보

## 📋 프로젝트 개요
- **프로젝트명**: Binance SMA Monitor
- **목적**: 바이낸스 선물 시장 15분봉 역배열 & SMA960 근처 자동 감지
- **생성일**: 2025-10-21
- **GitHub**: https://github.com/tedsungjinhwang-stack/binance-sma-monitor

---

## 🔐 AWS 정보

### EC2 인스턴스
- **인스턴스 ID**: i-0c4500ce6b235df02
- **퍼블릭 IP**: 54.180.88.4
- **리전**: ap-northeast-2 (서울)
- **인스턴스 타입**: t3.micro (프리 티어)
- **OS**: Ubuntu 22.04 LTS

### AWS 계정
- **Account ID**: 033566444122
- **Access Key ID**: AKIAQPUFXJJNIV2UDMGB
- **리전**: ap-northeast-2

### SSH 키
- **키 파일**: ~/binance-monitor-key.pem
- **키 이름**: binance-monitor-key

---

## 🔑 접속 정보

### EC2 SSH 접속
```bash
ssh -i ~/binance-monitor-key.pem ubuntu@54.180.88.4
```

### 로그 다운로드
```bash
~/download_monitor_logs.sh
```

---

## 📱 텔레그램 봇

### 봇 정보
- **Bot Token**: 8483398661:AAGwFzf1x-JXfRO5ZOy2FjqdtJdEgBFaXcY
- **Chat ID**: 5004236563
- **봇 이름**: @BotFather에서 생성

---

## ⚙️ 모니터링 설정

### 필터 조건
- **거래 방식**: USD-M PERPETUAL (USDT 무기한 선물)
- **최소 거래량**: 100M USD
- **최소 상승률**: 7%

### SMA 설정
- **기간**: 120, 240, 480, 960 (15분봉 기준)
- **타임프레임**: 15분봉
- **스캔 주기**: 900초 (15분)

### 시그널 조건
1. 역배열 (SMA120 > SMA240 > SMA480 > SMA960)
2. 종가가 SMA960의 ±5% 이내

---

## 🛠️ 주요 명령어

### 서비스 관리
```bash
# 상태 확인
sudo systemctl status sma-monitor

# 재시작
sudo systemctl restart sma-monitor

# 로그 보기
sudo journalctl -u sma-monitor -f
```

### 설정 변경
```bash
cd /home/ubuntu/binance-sma-monitor
nano config/config.yaml
sudo systemctl restart sma-monitor
```

---

## 💰 비용 정보

### 프리 티어 (1년간)
- **EC2**: 무료 (750시간/월)
- **스토리지**: 무료 (30GB/월)
- **기간**: 2025-10 ~ 2026-10

### 1년 후 예상 비용
- **EC2 t3.micro**: $10.37/월
- **EBS 8GB**: $0.77/월
- **총**: 약 $11~12/월

---

## 📂 파일 구조

```
binance-sma-monitor/
├── main.py                    # 메인 실행 파일
├── config/
│   ├── config.yaml           # 설정 파일 (텔레그램 정보 포함)
│   └── config.example.yaml   # 설정 예시
├── src/
│   ├── binance_api.py        # 바이낸스 API
│   ├── sma_calculator.py     # SMA 계산
│   ├── signal_detector.py    # 시그널 감지
│   ├── monitor.py            # 메인 모니터
│   └── notifier.py           # 텔레그램 알림
├── setup_ec2.sh              # EC2 자동 설치 스크립트
├── sma-monitor.service       # systemd 서비스
└── AWS_DEPLOYMENT_GUIDE.md   # 배포 가이드
```

---

## 🔄 업데이트 방법

### 로컬에서 코드 수정 후
```bash
# 1. GitHub에 푸시
cd /home/tedsungjinhwang/binance_sma_monitor
git add .
git commit -m "업데이트 내용"
git push origin main

# 2. EC2에서 업데이트
ssh -i ~/binance-monitor-key.pem ubuntu@54.180.88.4
cd binance-sma-monitor
git pull
sudo systemctl restart sma-monitor
```

---

## ⚠️ 백업 권장사항

### 정기 백업
1. **로그 다운로드**: 주 1회
   ```bash
   ~/download_monitor_logs.sh
   ```

2. **설정 파일 백업**: 변경 시마다
   ```bash
   scp -i ~/binance-monitor-key.pem \
     ubuntu@54.180.88.4:/home/ubuntu/binance-sma-monitor/config/config.yaml \
     ./config_backup.yaml
   ```

3. **키 파일 백업**: 안전한 곳에 보관
   - ~/binance-monitor-key.pem
   - USB 또는 클라우드에 별도 저장

---

## 📞 문제 해결

### 서비스가 안 돌아갈 때
```bash
ssh -i ~/binance-monitor-key.pem ubuntu@54.180.88.4
sudo journalctl -u sma-monitor -n 100
```

### 알림이 안 올 때
```bash
cd binance-sma-monitor
python3 test_telegram.py
```

### 인스턴스 재부팅
```bash
aws ec2 reboot-instances --instance-ids i-0c4500ce6b235df02
```

---

## 🎯 중요 체크리스트

- [x] GitHub에 코드 저장
- [x] EC2에서 24시간 실행 중
- [x] 텔레그램 알림 설정 완료
- [x] SSH 키 파일 백업
- [x] AWS Access Key 저장
- [x] 로그 다운로드 스크립트 생성

---

**마지막 업데이트**: 2025-10-21
**작성자**: Claude Code
