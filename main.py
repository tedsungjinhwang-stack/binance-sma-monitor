#!/usr/bin/env python3
"""
Binance SMA Monitor - 메인 실행 파일
15분봉 SMA 역배열 및 SMA960 근처 모니터링 시스템
"""
import os
import sys
import yaml
import logging
import argparse
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitor import SMAMonitor
from src.notifier import Notifier


def setup_logging(level: str = "INFO", log_file: str = None):
    """로깅 설정"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 로그 포맷
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 핸들러 설정
    handlers = []

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(console_handler)

    # 파일 핸들러
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(file_handler)

    # 루트 로거 설정
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def load_config(config_path: str = 'config/config.yaml') -> dict:
    """설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"설정 파일 파싱 오류: {e}")
        sys.exit(1)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Binance SMA Monitor - 15분봉 SMA 역배열 및 SMA960 근처 감지 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 실행 (설정 파일 기준)
  python main.py

  # 특정 심볼 테스트
  python main.py --test BTCUSDT

  # 알림 테스트
  python main.py --test-notification

  # 설정 정보 확인
  python main.py --status

설정:
  config/config.yaml 파일에서 모든 설정을 변경할 수 있습니다.
  - 모니터링 대상 코인
  - SMA 기간
  - 알림 방법 (콘솔, 텔레그램, 디스코드, 이메일)
  - 체크 주기
        """
    )

    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='설정 파일 경로 (기본: config/config.yaml)')
    parser.add_argument('--test', type=str, metavar='SYMBOL',
                       help='특정 심볼 테스트 (예: BTCUSDT)')
    parser.add_argument('--test-notification', action='store_true',
                       help='알림 테스트')
    parser.add_argument('--status', action='store_true',
                       help='현재 설정 상태 출력')

    args = parser.parse_args()

    # 설정 로드
    config = load_config(args.config)

    # 로깅 설정
    logging_config = config.get('LOGGING', {})
    setup_logging(
        level=logging_config.get('LEVEL', 'INFO'),
        log_file=logging_config.get('FILE') if logging_config.get('FILE') else None
    )

    logger = logging.getLogger(__name__)

    # 시작 메시지
    print("\n" + "=" * 60)
    print("Binance SMA Monitor")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # 모니터 초기화
    monitor = SMAMonitor(config)

    # 모드별 실행
    if args.test_notification:
        # 알림 테스트
        print("알림 테스트 실행 중...")
        monitor.notifier.test_notifications()

    elif args.test:
        # 특정 심볼 테스트
        symbol = args.test.upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        monitor.test_single_symbol(symbol)

    elif args.status:
        # 상태 출력
        monitor.update_symbol_list()
        monitor.print_status()

    else:
        # 메인 모니터링 실행
        monitor.run()


if __name__ == "__main__":
    main()
