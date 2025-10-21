#!/usr/bin/env python3
"""
GitHub Actions용 단일 실행 스크립트
한 번만 스캔하고 종료
"""
import os
import sys
import yaml
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitor import SMAMonitor


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def load_config():
    """설정 로드 (환경변수 우선)"""
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 환경변수에서 텔레그램 설정 읽기 (GitHub Secrets)
    if 'TELEGRAM_BOT_TOKEN' in os.environ:
        config['NOTIFICATION']['TELEGRAM']['BOT_TOKEN'] = os.environ['TELEGRAM_BOT_TOKEN']
    if 'TELEGRAM_CHAT_ID' in os.environ:
        config['NOTIFICATION']['TELEGRAM']['CHAT_ID'] = os.environ['TELEGRAM_CHAT_ID']

    return config


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Binance SMA Monitor - Single Scan")
    logger.info("=" * 60)

    config = load_config()
    monitor = SMAMonitor(config)

    # 심볼 리스트 업데이트
    monitor.update_symbol_list()

    # 한 번만 스캔
    signal_count = monitor.scan_all_symbols()

    if signal_count > 0:
        logger.info(f"✓ {signal_count}개 시그널 발견!")
    else:
        logger.info("시그널 없음")

    logger.info("스캔 완료")


if __name__ == "__main__":
    main()
