"""
메인 모니터링 모듈
실시간 모니터링 및 시그널 감지
"""
import time
from typing import List, Dict
import logging
from .binance_api import BinanceAPI
from .sma_calculator import SMACalculator
from .signal_detector import SignalDetector
from .notifier import Notifier

logger = logging.getLogger(__name__)


class SMAMonitor:
    """SMA 모니터"""

    def __init__(self, config: Dict):
        """
        초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config

        # Binance API 초기화
        binance_config = config.get('BINANCE', {})
        self.api = BinanceAPI(
            api_key=binance_config.get('API_KEY', ''),
            api_secret=binance_config.get('API_SECRET', ''),
            testnet=binance_config.get('TESTNET', False)
        )

        # 모니터링 설정
        monitor_config = config.get('MONITOR', {})
        self.interval = monitor_config.get('INTERVAL', 60)
        self.timeframe = monitor_config.get('TIMEFRAME', '15m')

        # 코인 필터 설정
        coin_filter = monitor_config.get('COIN_FILTER', {})
        self.coin_filter_mode = coin_filter.get('MODE', 'FILTERED')
        self.top_n = coin_filter.get('TOP_N', 50)
        self.specific_coins = coin_filter.get('SPECIFIC_COINS', [])
        self.min_volume_usd = coin_filter.get('MIN_VOLUME_USD', 100_000_000)
        self.min_price_change_pct = coin_filter.get('MIN_PRICE_CHANGE_PCT', 7.0)

        # SMA 계산기
        sma_config = config.get('SMA', {})
        sma_periods = sma_config.get('PERIODS', [120, 240, 480, 960])
        self.sma_calculator = SMACalculator(periods=sma_periods)

        # 시그널 감지기
        signal_config = config.get('SIGNAL', {})
        breakout_config = signal_config.get('BREAKOUT', {})
        self.signal_detector = SignalDetector(
            target_sma=breakout_config.get('TARGET_SMA', 960),
            confirm_candles=breakout_config.get('CONFIRM_CANDLES', 1),
            cooldown=signal_config.get('COOLDOWN', 3600)
        )
        self.breakout_type = breakout_config.get('TYPE', 'CLOSE')

        # 모멘텀 설정
        momentum_config = signal_config.get('MOMENTUM', {})
        self.momentum_enabled = momentum_config.get('ENABLED', False)
        self.momentum_timeframe = momentum_config.get('TIMEFRAME', '24h')  # 4h, 6h, 12h, 24h
        self.momentum_min_volume = momentum_config.get('MIN_VOLUME_USD', 100_000_000)
        self.momentum_min_price_change = momentum_config.get('MIN_PRICE_CHANGE_PCT', 15.0)

        # 알림기
        notification_config = config.get('NOTIFICATION', {})
        self.notifier = Notifier(notification_config)

        # 모니터링할 심볼 리스트
        self.symbols: List[str] = []

        logger.info("SMA 모니터 초기화 완료")

    def update_symbol_list(self):
        """모니터링할 심볼 리스트 업데이트"""
        logger.info("심볼 리스트 업데이트 중...")

        if self.coin_filter_mode == 'ALL':
            # ALL 모드: 3일 상승률 기반 필터 사용
            self.symbols = self.api.get_filtered_symbols_by_momentum(
                min_volume_usd=2_000_000,
                min_3day_change_pct=8.0
            )
        elif self.coin_filter_mode == 'TOP_VOLUME':
            self.symbols = self.api.get_top_volume_symbols(self.top_n)
        elif self.coin_filter_mode == 'FILTERED':
            self.symbols = self.api.get_filtered_symbols(
                min_volume_usd=self.min_volume_usd,
                min_price_change_pct=self.min_price_change_pct
            )
        elif self.coin_filter_mode == 'SPECIFIC':
            self.symbols = self.specific_coins
        else:
            logger.warning(f"알 수 없는 필터 모드: {self.coin_filter_mode}. 3일 모멘텀 필터 사용")
            self.symbols = self.api.get_filtered_symbols_by_momentum(
                min_volume_usd=2_000_000,
                min_3day_change_pct=8.0
            )

        logger.info(f"모니터링 대상: {len(self.symbols)}개 심볼")

    def analyze_symbol(self, symbol: str) -> bool:
        """
        단일 심볼 분석

        Args:
            symbol: 심볼

        Returns:
            시그널 발생 여부
        """
        signal_detected = False

        try:
            # 1. 역배열 시그널 체크
            # 캔들 데이터 가져오기 (SMA 계산에 충분한 양)
            limit = self.sma_calculator.max_period + 100
            df = self.api.get_klines(symbol, interval=self.timeframe, limit=limit)

            if df.empty:
                logger.debug(f"{symbol}: 데이터 없음")
            else:
                # SMA 계산
                df_with_sma = self.sma_calculator.calculate_all_smas(df)

                # 현재 SMA 값들
                sma_values = self.sma_calculator.get_current_sma_values(df_with_sma)

                if sma_values:
                    # 사용 가능한 target SMA 결정 (960만)
                    actual_target_sma = self.sma_calculator.get_available_target_sma(sma_values)

                    if actual_target_sma != 0:
                        # 역배열 확인
                        reverse_aligned, reverse_type = self.sma_calculator.check_reverse_alignment_flexible(sma_values, actual_target_sma)

                        # 디버그: target SMA 근처 체크
                        current_price = df_with_sma.iloc[-1]['close']
                        target_sma_value = sma_values.get(actual_target_sma)
                        if target_sma_value:
                            diff_pct = ((current_price - target_sma_value) / target_sma_value) * 100
                            lower_bound = target_sma_value * 0.95
                            upper_bound = target_sma_value * 1.05
                            if lower_bound <= current_price <= upper_bound:
                                reverse_label = f"✅({reverse_type})" if reverse_aligned else "❌"
                                logger.info(f"{symbol}: SMA{actual_target_sma} 근처! 종가={current_price:.4f}, SMA{actual_target_sma}={target_sma_value:.4f}, 차이={diff_pct:+.2f}%, 역배열={reverse_label}")

                        # 역배열 시그널 분석
                        signal_info = self.signal_detector.analyze_signal(
                            symbol=symbol,
                            df=df_with_sma,
                            sma_values=sma_values,
                            reverse_aligned=reverse_aligned,
                            reverse_type=reverse_type,
                            actual_target_sma=actual_target_sma,
                            breakout_type=self.breakout_type
                        )

                        if signal_info:
                            # 거래대금 순위 및 거래대금 추가
                            volume_info = self.api.get_volume_rank(symbol)
                            if volume_info:
                                signal_info['volume_rank'] = volume_info['rank']
                                signal_info['quote_volume'] = volume_info['quote_volume']

                            # 역배열 시그널 발생!
                            summary = self.signal_detector.get_signal_summary(signal_info)
                            self.notifier.send_signal_alert(signal_info, summary)
                            signal_detected = True

            # 2. 모멘텀 시그널 체크 (활성화된 경우)
            if self.momentum_enabled and not df.empty:
                momentum_signal = self.signal_detector.analyze_momentum_signal_rolling(
                    symbol=symbol,
                    df=df,
                    timeframe=self.momentum_timeframe,
                    min_volume_usd=self.momentum_min_volume,
                    min_price_change_pct=self.momentum_min_price_change
                )

                if momentum_signal:
                    # 거래대금 순위 및 거래대금 추가
                    volume_info = self.api.get_volume_rank(symbol)
                    if volume_info:
                        momentum_signal['volume_rank'] = volume_info['rank']
                        momentum_signal['quote_volume'] = volume_info['quote_volume']

                    # 모멘텀 시그널 발생!
                    summary = self.signal_detector.get_signal_summary(momentum_signal)
                    self.notifier.send_signal_alert(momentum_signal, summary)
                    signal_detected = True

            return signal_detected

        except Exception as e:
            logger.error(f"{symbol} 분석 중 오류: {e}")
            return False

    def scan_all_symbols(self) -> int:
        """
        모든 심볼 스캔

        Returns:
            발견된 시그널 수
        """
        logger.info(f"{len(self.symbols)}개 심볼 스캔 시작...")

        signal_count = 0

        for i, symbol in enumerate(self.symbols, 1):
            logger.debug(f"[{i}/{len(self.symbols)}] {symbol} 분석 중...")

            if self.analyze_symbol(symbol):
                signal_count += 1

            # API 레이트 리밋 방지
            time.sleep(0.1)

        logger.info(f"스캔 완료: {signal_count}개 시그널 발견")
        return signal_count

    def run(self):
        """메인 모니터링 루프"""
        logger.info("=" * 60)
        logger.info("바이낸스 SMA 모니터 시작")
        logger.info("=" * 60)

        self.notifier.send_system_message("모니터링 시작!", "INFO")

        # 초기 심볼 리스트 업데이트
        self.update_symbol_list()

        iteration = 0

        try:
            while True:
                iteration += 1
                logger.info(f"\n[반복 #{iteration}] 스캔 시작...")

                # 주기적으로 심볼 리스트 업데이트 (매 10회)
                if iteration % 10 == 0:
                    self.update_symbol_list()

                # 전체 스캔
                signal_count = self.scan_all_symbols()

                if signal_count > 0:
                    logger.info(f"✓ {signal_count}개 시그널 발견 및 알림 전송 완료")
                else:
                    logger.info("시그널 없음")

                # 대기
                logger.info(f"{self.interval}초 대기 중...")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("\n사용자에 의해 중단됨")
            self.notifier.send_system_message("모니터링 중단", "WARNING")
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            self.notifier.send_system_message(f"오류 발생: {e}", "ERROR")
            raise

    def test_single_symbol(self, symbol: str):
        """
        단일 심볼 테스트

        Args:
            symbol: 테스트할 심볼
        """
        logger.info(f"=" * 60)
        logger.info(f"{symbol} 테스트 분석")
        logger.info(f"=" * 60)

        self.analyze_symbol(symbol)

    def print_status(self):
        """현재 상태 출력"""
        print("\n" + "=" * 60)
        print("모니터링 상태")
        print("=" * 60)
        print(f"모니터링 심볼 수: {len(self.symbols)}")
        print(f"체크 주기: {self.interval}초")
        print(f"시간 프레임: {self.timeframe}")
        print(f"SMA 기간: {self.sma_calculator.periods}")
        print(f"돌파 기준: SMA{self.signal_detector.target_sma}")
        print(f"쿨다운: {self.signal_detector.cooldown}초")
        print(f"알림 이력: {len(self.signal_detector.last_alert_time)}개")
        print("=" * 60 + "\n")
