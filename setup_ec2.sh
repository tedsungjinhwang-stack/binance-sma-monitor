#!/bin/bash
# EC2 인스턴스 자동 설정 스크립트

set -e

echo "======================================"
echo "Binance SMA Monitor - EC2 Setup"
echo "======================================"

# 1. 시스템 업데이트
echo "[1/6] 시스템 업데이트 중..."
sudo apt update -y
sudo apt upgrade -y

# 2. Python 및 pip 설치
echo "[2/6] Python 설치 중..."
sudo apt install -y python3 python3-pip git

# 3. 프로젝트 클론 (이미 있으면 스킵)
echo "[3/6] 프로젝트 설정 중..."
if [ ! -d "/home/ubuntu/binance_sma_monitor" ]; then
    cd /home/ubuntu
    git clone https://github.com/tedsungjinhwang-stack/binance-sma-monitor.git binance_sma_monitor
    cd binance_sma_monitor
else
    cd /home/ubuntu/binance_sma_monitor
    git pull
fi

# 4. Python 패키지 설치
echo "[4/6] Python 패키지 설치 중..."
pip3 install --break-system-packages -r requirements.txt

# 5. 설정 파일 확인
echo "[5/6] 설정 파일 확인 중..."
if [ ! -f "config/config.yaml" ]; then
    echo "오류: config/config.yaml 파일이 없습니다!"
    echo "config/config.yaml 파일을 먼저 설정해주세요."
    exit 1
fi

# 텔레그램 설정 확인
echo "텔레그램 설정 확인 중..."
if grep -q 'BOT_TOKEN: ""' config/config.yaml; then
    echo "경고: 텔레그램 BOT_TOKEN이 설정되지 않았습니다."
    echo "config/config.yaml에서 텔레그램 설정을 확인해주세요."
fi

# 6. systemd 서비스 설정
echo "[6/6] systemd 서비스 설정 중..."
sudo cp sma-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sma-monitor.service

echo ""
echo "======================================"
echo "설치 완료!"
echo "======================================"
echo ""
echo "다음 명령어로 모니터링을 시작하세요:"
echo "  sudo systemctl start sma-monitor"
echo ""
echo "상태 확인:"
echo "  sudo systemctl status sma-monitor"
echo ""
echo "로그 확인:"
echo "  sudo journalctl -u sma-monitor -f"
echo ""
