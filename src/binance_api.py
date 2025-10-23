"""
Binance API 연결 모듈
바이낸스 선물 시장 데이터 수집
"""
import time
from typing import List, Dict, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BinanceAPI:
    """바이낸스 API 클라이언트"""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        """
        초기화

        Args:
            api_key: API 키 (읽기 전용도 가능, 비어있어도 됨)
            api_secret: API 시크릿
            testnet: 테스트넷 사용 여부
        """
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            logger.info(f"바이낸스 API 연결 완료 (Testnet: {testnet})")
        except Exception as e:
            logger.error(f"바이낸스 API 연결 실패: {e}")
            raise

    def get_futures_symbols(self) -> List[str]:
        """
        USDT 선물 마켓의 모든 심볼 가져오기

        Returns:
            USDT 선물 심볼 리스트
        """
        try:
            exchange_info = self.client.futures_exchange_info()
            symbols = [
                s['symbol']
                for s in exchange_info['symbols']
                if s['symbol'].endswith('USDT')
                   and s['status'] == 'TRADING'
                   and s['contractType'] == 'PERPETUAL'
            ]
            logger.info(f"총 {len(symbols)}개 USDT 선물 심볼 발견")
            return symbols
        except BinanceAPIException as e:
            logger.error(f"심볼 목록 가져오기 실패: {e}")
            return []

    def get_filtered_symbols(self, min_volume_usd: float = 100_000_000, min_price_change_pct: float = 7.0) -> List[str]:
        """
        사전필터 적용하여 심볼 가져오기
        - TetherUS PERPETUAL CONTRACT 종목
        - 24시간 거래량 100M USD 초과
        - 24시간 상승률 7% 이상

        Args:
            min_volume_usd: 최소 거래량 (USD)
            min_price_change_pct: 최소 상승률 (%)

        Returns:
            필터링된 심볼 리스트
        """
        try:
            # 거래소 정보 가져오기 (contractType 확인용)
            exchange_info = self.client.futures_exchange_info()
            perpetual_symbols = {
                s['symbol']
                for s in exchange_info['symbols']
                if s['symbol'].endswith('USDT')
                   and s['status'] == 'TRADING'
                   and s['contractType'] == 'PERPETUAL'
            }
            logger.debug(f"USDT 무기한 선물 계약: {len(perpetual_symbols)}개")

            # 24시간 티커 데이터 가져오기
            tickers = self.client.futures_ticker()

            filtered_symbols = []

            for ticker in tickers:
                symbol = ticker['symbol']

                # 1. USDT PERPETUAL 선물만 필터링
                if symbol not in perpetual_symbols:
                    continue

                try:
                    quote_volume = float(ticker.get('quoteVolume', 0))
                    price_change_pct = float(ticker.get('priceChangePercent', 0))

                    # 2. 거래량 필터 (100M USD 초과)
                    if quote_volume < min_volume_usd:
                        continue

                    # 3. 상승률 필터 (7% 이상)
                    if price_change_pct < min_price_change_pct:
                        continue

                    filtered_symbols.append(symbol)
                    logger.debug(f"{symbol}: 거래량=${quote_volume:,.0f}, 상승률={price_change_pct:+.2f}%")

                except (ValueError, TypeError) as e:
                    logger.debug(f"{symbol} 데이터 파싱 오류: {e}")
                    continue

            # 거래량 기준으로 정렬 (많은 순)
            tickers_dict = {t['symbol']: float(t.get('quoteVolume', 0)) for t in tickers if t['symbol'] in filtered_symbols}
            filtered_symbols = sorted(filtered_symbols, key=lambda s: tickers_dict.get(s, 0), reverse=True)

            logger.info(f"사전필터 통과: {len(filtered_symbols)}개 심볼 "
                       f"(USD-M PERPETUAL, 거래량≥${min_volume_usd/1_000_000:.0f}M, 상승률≥{min_price_change_pct:+.0f}%)")

            if filtered_symbols:
                logger.info(f"필터링된 심볼 예시: {filtered_symbols[:10]}")

            return filtered_symbols

        except BinanceAPIException as e:
            logger.error(f"필터링된 심볼 가져오기 실패: {e}")
            return []

    def get_top_volume_symbols(self, top_n: int = 50) -> List[str]:
        """
        24시간 거래량 기준 상위 N개 심볼 가져오기 (레거시 함수)

        Args:
            top_n: 상위 N개

        Returns:
            심볼 리스트
        """
        try:
            tickers = self.client.futures_ticker()

            # USDT 선물만 필터링
            usdt_tickers = [
                t for t in tickers
                if t['symbol'].endswith('USDT')
            ]

            # 거래량(USDT) 기준 정렬
            sorted_tickers = sorted(
                usdt_tickers,
                key=lambda x: float(x.get('quoteVolume', 0)),
                reverse=True
            )

            symbols = [t['symbol'] for t in sorted_tickers[:top_n]]
            logger.info(f"거래량 상위 {top_n}개 심볼: {symbols[:5]}...")

            return symbols

        except BinanceAPIException as e:
            logger.error(f"거래량 상위 심볼 가져오기 실패: {e}")
            return []

    def get_klines(self, symbol: str, interval: str = '5m', limit: int = 1000) -> pd.DataFrame:
        """
        K라인(캔들) 데이터 가져오기

        Args:
            symbol: 심볼 (예: BTCUSDT)
            interval: 시간 프레임 (1m, 3m, 5m, 15m, 1h, 4h, 1d 등)
            limit: 가져올 캔들 수 (최대 1500)

        Returns:
            OHLCV 데이터프레임
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            # DataFrame으로 변환
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # 데이터 타입 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            df.set_index('timestamp', inplace=True)

            return df[['open', 'high', 'low', 'close', 'volume']]

        except BinanceAPIException as e:
            logger.error(f"{symbol} 캔들 데이터 가져오기 실패: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        현재 가격 가져오기

        Args:
            symbol: 심볼

        Returns:
            현재 가격
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"{symbol} 현재 가격 가져오기 실패: {e}")
            return None

    def get_24h_stats(self, symbol: str) -> Optional[Dict]:
        """
        24시간 통계 가져오기

        Args:
            symbol: 심볼

        Returns:
            24시간 통계 딕셔너리
        """
        try:
            stats = self.client.futures_ticker(symbol=symbol)
            return {
                'price_change_percent': float(stats['priceChangePercent']),
                'volume': float(stats['volume']),
                'quote_volume': float(stats['quoteVolume']),
                'high': float(stats['highPrice']),
                'low': float(stats['lowPrice']),
            }
        except BinanceAPIException as e:
            logger.error(f"{symbol} 24시간 통계 가져오기 실패: {e}")
            return None

    def get_volume_change_pct(self, symbol: str) -> Optional[float]:
        """
        24시간 볼륨 변화율 계산 (오늘 vs 어제)

        Args:
            symbol: 심볼

        Returns:
            볼륨 변화율 (%) 또는 None
        """
        try:
            # 1일봉 3개 가져오기 (오늘 진행중, 어제, 그저께)
            klines = self.client.futures_klines(
                symbol=symbol,
                interval='1d',
                limit=3
            )

            if len(klines) < 2:
                logger.debug(f"{symbol}: 볼륨 변화 계산 불가 (데이터 부족)")
                return None

            # 최근 2일 볼륨 비교
            today_volume = float(klines[-1][7])  # quote_volume (USDT 단위)
            yesterday_volume = float(klines[-2][7])

            if yesterday_volume == 0:
                return None

            volume_change_pct = ((today_volume - yesterday_volume) / yesterday_volume) * 100

            return volume_change_pct

        except (BinanceAPIException, IndexError, ValueError) as e:
            logger.error(f"{symbol} 볼륨 변화 계산 실패: {e}")
            return None
