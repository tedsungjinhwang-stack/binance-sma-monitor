# Binance SMA Monitor

바이낸스 USDT 선물 시장에서 5분봉 SMA 역배열 및 돌파를 실시간으로 감지하는 모니터링 시스템입니다.

## 주요 기능

- ✅ 바이낸스 USDT Perpetual 선물 시장 모니터링
- ✅ 5분봉 기준 SMA(120, 240, 480, 960) 계산
- ✅ SMA 역배열 감지 (SMA120 > SMA240 > SMA480 > SMA960)
- ✅ SMA960선 상향 돌파 감지
- ✅ 다양한 알림 방법 (콘솔, 텔레그램, 디스코드, 이메일)
- ✅ 중복 알림 방지 (쿨다운 기능)
- ✅ 거래량 상위 코인 자동 필터링

## 설치

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 구성

`config/config.yaml` 파일을 열어 다음 항목들을 설정하세요:

#### 바이낸스 API (선택사항)
```yaml
BINANCE:
  API_KEY: ""  # 읽기 전용 권한만 있으면 됨 (또는 비워두기)
  API_SECRET: ""
```
> **참고**: API 키가 없어도 공개 데이터 조회가 가능합니다.

#### 모니터링 설정
```yaml
MONITOR:
  INTERVAL: 60  # 체크 주기 (초)
  COIN_FILTER:
    MODE: "TOP_VOLUME"  # ALL, TOP_VOLUME, SPECIFIC
    TOP_N: 50  # 거래량 상위 N개 코인
```

#### 알림 설정

**텔레그램 알림** (권장)
```yaml
NOTIFICATION:
  METHODS:
    TELEGRAM: true
  TELEGRAM:
    BOT_TOKEN: "your_bot_token"  # @BotFather에서 발급
    CHAT_ID: "your_chat_id"      # @userinfobot에서 확인
```

**디스코드 웹훅**
```yaml
NOTIFICATION:
  METHODS:
    DISCORD: true
  DISCORD:
    WEBHOOK_URL: "your_webhook_url"
```

## 사용법

### 기본 실행

```bash
python main.py
```

실시간으로 모니터링을 시작하고, 조건을 만족하는 코인이 발견되면 알림을 전송합니다.

### 특정 코인 테스트

```bash
python main.py --test BTCUSDT
```

특정 코인의 현재 상태를 즉시 분석합니다.

### 알림 테스트

```bash
python main.py --test-notification
```

설정한 알림 방법들이 제대로 작동하는지 테스트합니다.

### 설정 상태 확인

```bash
python main.py --status
```

현재 모니터링 설정과 대상 코인 목록을 출력합니다.

## 시그널 조건

다음 조건을 **모두** 만족할 때 알림이 발송됩니다:

1. **SMA 역배열**: SMA120 > SMA240 > SMA480 > SMA960
2. **960선 돌파**: 이전 캔들 종가 < SMA960, 현재 캔들 종가 > SMA960
3. **쿨다운**: 같은 코인에 대해 마지막 알림 후 1시간(설정 가능) 경과

## SMA 기간 설명

5분봉 기준:
- **SMA120** = 10시간
- **SMA240** = 20시간
- **SMA480** = 40시간 (약 1.7일)
- **SMA960** = 80시간 (약 3.3일)

## 프로젝트 구조

```
binance_sma_monitor/
├── config/
│   └── config.yaml          # 설정 파일
├── src/
│   ├── binance_api.py       # 바이낸스 API 연결
│   ├── sma_calculator.py    # SMA 계산
│   ├── signal_detector.py   # 시그널 감지
│   ├── notifier.py          # 알림 전송
│   └── monitor.py           # 메인 모니터링 로직
├── logs/                    # 로그 파일 (자동 생성)
├── main.py                  # 실행 파일
├── requirements.txt         # 필수 패키지 목록
└── README.md
```

## 텔레그램 봇 설정 방법

### 1. 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/BotFather) 검색
2. `/newbot` 명령 입력
3. 봇 이름과 username 설정
4. 받은 **BOT TOKEN** 복사

### 2. Chat ID 확인

1. [@userinfobot](https://t.me/userinfobot) 검색
2. 봇 시작하면 자동으로 **Chat ID** 표시
3. Chat ID를 `config.yaml`에 입력

### 3. 봇 시작

1. 생성한 봇을 검색하여 대화 시작
2. `/start` 명령 입력
3. `python main.py --test-notification` 실행하여 알림 테스트

## 주의사항

- 이 시스템은 **참고용**이며, 투자 결정의 책임은 본인에게 있습니다
- API 레이트 리밋을 고려하여 적절한 체크 주기를 설정하세요
- 과도한 알림을 방지하기 위해 쿨다운 기능을 활용하세요
- 실제 거래는 반드시 본인의 판단으로 진행하세요

## 문제 해결

### 패키지 설치 오류

```bash
# python-binance 설치 오류 시
pip install python-binance --upgrade

# 전체 재설치
pip install -r requirements.txt --force-reinstall
```

### 텔레그램 알림이 안 오는 경우

1. BOT TOKEN과 CHAT ID가 정확한지 확인
2. 봇과 대화를 시작했는지 확인 (`/start` 입력)
3. `python main.py --test-notification` 실행하여 오류 메시지 확인

### "No module named 'binance'" 오류

```bash
pip install python-binance
```

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

---

**경고**: 암호화폐 거래는 높은 리스크를 동반합니다. 이 도구는 교육 및 참고 목적으로만 사용하세요.
