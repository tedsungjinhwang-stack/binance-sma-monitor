"""
시그널 감지 모듈
역배열 및 SMA 돌파 감지
"""
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SignalDetector:
    """시그널 감지기"""

    def __init__(self, target_sma: int = 480, confirm_candles: int = 1, cooldown: int = 3600):
        """
        초기화

        Args:
            target_sma: 돌파 기준 SMA 기간
            confirm_candles: 돌파 확인할 캔들 수
            cooldown: 같은 코인 재알림 대기 시간 (초)
        """
        self.target_sma = target_sma
        self.target_sma_col = f'sma_{target_sma}'
        self.confirm_candles = confirm_candles
        self.cooldown = cooldown

        # 알림 이력 (중복 방지용)
        self.last_alert_time: Dict[str, datetime] = {}

        logger.info(f"시그널 감지기 초기화: SMA{target_sma} 돌파, {confirm_candles}캔들 확인, "
                   f"{cooldown}초 쿨다운")

    def check_near_target_sma(self, df: pd.DataFrame, target_sma: int, tolerance_pct: float = 5.0) -> bool:
        """
        종가가 target SMA의 ±tolerance_pct% 이내인지 확인

        Args:
            df: SMA가 계산된 데이터프레임
            target_sma: 기준 SMA (480, 1시간봉)
            tolerance_pct: 허용 오차 퍼센트 (기본 5%)

        Returns:
            target SMA 근처 여부
        """
        target_sma_col = f'sma_{target_sma}'

        if df.empty or target_sma_col not in df.columns:
            return False

        # 현재 캔들
        current_candle = df.iloc[-1]
        current_close = current_candle['close']
        current_sma = current_candle[target_sma_col]

        # NaN 체크
        if pd.isna(current_close) or pd.isna(current_sma):
            return False

        # 종가가 target SMA의 ±tolerance_pct% 이내인지 확인
        lower_bound = current_sma * (1 - tolerance_pct / 100)
        upper_bound = current_sma * (1 + tolerance_pct / 100)

        is_near = lower_bound <= current_close <= upper_bound

        return is_near

    def check_breakout_close(self, df: pd.DataFrame, reverse_aligned: bool) -> bool:
        """
        종가 기준 돌파 확인

        Args:
            df: SMA가 계산된 데이터프레임
            reverse_aligned: 역배열 확인 여부

        Returns:
            돌파 여부
        """
        if df.empty or self.target_sma_col not in df.columns:
            return False

        # 역배열이 아니면 False
        if not reverse_aligned:
            return False

        # 최신 캔들들 확인
        recent_candles = df.tail(self.confirm_candles + 1)

        if len(recent_candles) < self.confirm_candles + 1:
            return False

        # 이전 캔들 (돌파 전)
        prev_candle = recent_candles.iloc[-self.confirm_candles - 1]
        prev_close = prev_candle['close']
        prev_sma = prev_candle[self.target_sma_col]

        # 현재 캔들 (돌파 후)
        current_candle = recent_candles.iloc[-1]
        current_close = current_candle['close']
        current_sma = current_candle[self.target_sma_col]

        # NaN 체크
        if pd.isna(prev_close) or pd.isna(prev_sma) or pd.isna(current_close) or pd.isna(current_sma):
            return False

        # 돌파 조건: 이전 종가 < SMA, 현재 종가 > SMA
        breakout = prev_close < prev_sma and current_close > current_sma

        if breakout:
            logger.info(f"돌파 감지! 이전: {prev_close:.4f} < {prev_sma:.4f}, "
                       f"현재: {current_close:.4f} > {current_sma:.4f}")

        return breakout

    def check_breakout_body(self, df: pd.DataFrame, reverse_aligned: bool) -> bool:
        """
        캔들 전체(고가) 기준 돌파 확인

        Args:
            df: SMA가 계산된 데이터프레임
            reverse_aligned: 역배열 확인 여부

        Returns:
            돌파 여부
        """
        if df.empty or self.target_sma_col not in df.columns:
            return False

        if not reverse_aligned:
            return False

        recent_candles = df.tail(self.confirm_candles + 1)

        if len(recent_candles) < self.confirm_candles + 1:
            return False

        # 이전 캔들의 고가가 SMA 아래
        prev_candle = recent_candles.iloc[-self.confirm_candles - 1]
        prev_high = prev_candle['high']
        prev_sma = prev_candle[self.target_sma_col]

        # 현재 캔들이 SMA 돌파
        current_candle = recent_candles.iloc[-1]
        current_high = current_candle['high']
        current_low = current_candle['low']
        current_sma = current_candle[self.target_sma_col]

        if pd.isna(prev_high) or pd.isna(prev_sma) or pd.isna(current_high) or pd.isna(current_sma):
            return False

        # 돌파 조건: 이전 고가 < SMA, 현재 캔들이 SMA를 관통
        breakout = prev_high < prev_sma and current_low < current_sma < current_high

        return breakout

    def should_send_alert(self, symbol: str) -> bool:
        """
        알림을 보내야 하는지 확인 (쿨다운 체크)

        Args:
            symbol: 심볼

        Returns:
            알림 전송 여부
        """
        now = datetime.now()

        if symbol not in self.last_alert_time:
            return True

        last_time = self.last_alert_time[symbol]
        elapsed = (now - last_time).total_seconds()

        if elapsed >= self.cooldown:
            return True

        logger.debug(f"{symbol}: 쿨다운 중 ({elapsed:.0f}초/{self.cooldown}초)")
        return False

    def record_alert(self, symbol: str):
        """
        알림 기록 (쿨다운 시작)

        Args:
            symbol: 심볼
        """
        self.last_alert_time[symbol] = datetime.now()
        logger.debug(f"{symbol}: 알림 기록됨")

    def analyze_signal(self, symbol: str, df: pd.DataFrame, sma_values: Dict[int, float],
                      reverse_aligned: bool, reverse_type: str, actual_target_sma: int,
                      breakout_type: str = "CLOSE") -> Optional[Dict]:
        """
        종합 시그널 분석

        Args:
            symbol: 심볼
            df: SMA가 계산된 데이터프레임
            sma_values: 현재 SMA 값들
            reverse_aligned: 역배열 여부
            reverse_type: 역배열 타입 ("FULL", "PARTIAL", None)
            actual_target_sma: 실제 사용된 target SMA (480, 1시간봉)
            breakout_type: 돌파 타입 (CLOSE, BODY, NEAR)

        Returns:
            시그널 정보 딕셔너리 (시그널 없으면 None)
        """
        # target SMA가 0이면 (데이터 부족) 스킵
        if actual_target_sma == 0:
            return None

        # target SMA 근처 확인
        near_target = self.check_near_target_sma(df, actual_target_sma, tolerance_pct=5.0)

        # 조건: 역배열 AND target SMA 근처
        if not (reverse_aligned and near_target):
            return None

        # 추가 필터: 24시간 모멘텀 체크 (상승률 5% + 거래량 10M)
        candles_24h = 24  # 24시간 = 24개 1시간봉

        if len(df) < candles_24h + 1:
            return None

        # 현재 캔들 정보
        current_candle = df.iloc[-1]
        current_price = current_candle['close']

        # 24시간 전 가격
        past_candle = df.iloc[-(candles_24h + 1)]
        past_price = past_candle['close']

        # 24시간 상승률 계산
        price_change_24h = ((current_price - past_price) / past_price) * 100

        # 24시간 거래량 계산
        df_temp = df.copy()
        df_temp['quote_volume'] = df_temp['volume'] * df_temp['close']
        volume_24h = df_temp.tail(candles_24h)['quote_volume'].sum()

        # 24시간 모멘텀 필터: 상승률 5% 이상 AND 거래량 10M 이상
        if price_change_24h < 5.0 or volume_24h < 10_000_000:
            return None

        # 쿨다운 확인
        if not self.should_send_alert(symbol):
            return None

        current_time = df.index[-1]

        # 시그널 타입 (480만 사용, 1시간봉)
        signal_type = "REVERSE_ALIGNED_AND_NEAR_SMA480"

        # 시그널 정보 생성
        signal_info = {
            'symbol': symbol,
            'timestamp': current_time,
            'price': current_price,
            'sma_values': sma_values,
            'target_sma': sma_values.get(actual_target_sma),
            'target_sma_period': actual_target_sma,
            'signal_type': signal_type,
            'reverse_aligned': reverse_aligned,
            'reverse_type': reverse_type,
            'near_target': near_target,
        }

        # 알림 기록
        self.record_alert(symbol)

        logger.info(f"시그널 발생: {symbol} @ {current_price:.4f} (타입: {signal_type}, 역배열: {reverse_type})")

        return signal_info

    def analyze_momentum_signal_rolling(self, symbol: str, df: pd.DataFrame, timeframe: str,
                                       min_volume_usd: float, min_price_change_pct: float) -> Optional[Dict]:
        """
        모멘텀 시그널 분석 (Rolling 기준)

        Args:
            symbol: 심볼
            df: 캔들 데이터프레임
            timeframe: 시간 기준 (4h, 6h, 12h, 24h)
            min_volume_usd: 최소 거래량 (USD)
            min_price_change_pct: 최소 상승률 (%)

        Returns:
            시그널 정보 딕셔너리 (시그널 없으면 None)
        """
        # 쿨다운 확인
        if not self.should_send_alert(symbol):
            return None

        if df.empty:
            return None

        # 시간 기준에 따른 캔들 수 매핑
        timeframe_candles = {
            '4h': 16,   # 4시간 = 16개 15분봉
            '6h': 24,   # 6시간 = 24개 15분봉
            '12h': 48,  # 12시간 = 48개 15분봉
            '24h': 96,  # 24시간 = 96개 15분봉
        }

        candles = timeframe_candles.get(timeframe, 96)

        # 충분한 데이터가 있는지 확인
        if len(df) < candles + 1:
            return None

        # 현재 캔들
        current_candle = df.iloc[-1]
        current_price = current_candle['close']

        # N시간 전 가격
        past_candle = df.iloc[-(candles + 1)]
        past_price = past_candle['close']

        # 상승률 계산
        price_change_pct = ((current_price - past_price) / past_price) * 100

        # 거래량 계산 (N시간)
        df['quote_volume'] = df['volume'] * df['close']
        recent_volume = df.tail(candles)['quote_volume'].sum()

        # 조건 확인
        # 1. 상승률 체크
        if price_change_pct < min_price_change_pct:
            return None

        # 2. 거래량 체크
        if recent_volume < min_volume_usd:
            return None

        # 모든 조건 만족! 시그널 생성
        signal_info = {
            'symbol': symbol,
            'timestamp': df.index[-1],
            'signal_type': f'STRONG_MOMENTUM_{timeframe.upper()}',
            'timeframe': timeframe,
            'quote_volume': recent_volume,
            'price_change_percent': price_change_pct,
            'current_price': current_price,
        }

        # 알림 기록
        self.record_alert(symbol)

        logger.info(f"모멘텀 시그널 발생: {symbol} ({timeframe} 상승률: {price_change_pct:+.2f}%)")

        return signal_info

    def analyze_momentum_signal(self, symbol: str, stats: Dict,
                                min_volume_usd: float, min_price_change_pct: float) -> Optional[Dict]:
        """
        모멘텀 시그널 분석 (강력한 상승 모멘텀)

        Args:
            symbol: 심볼
            stats: 24시간 통계 정보
            min_volume_usd: 최소 거래량 (USD)
            min_price_change_pct: 최소 상승률 (%)

        Returns:
            시그널 정보 딕셔너리 (시그널 없으면 None)
        """
        # 쿨다운 확인
        if not self.should_send_alert(symbol):
            return None

        # 조건 확인
        quote_volume = stats.get('quote_volume', 0)
        price_change_pct = stats.get('price_change_percent', 0)

        # 1. 거래량 체크
        if quote_volume < min_volume_usd:
            return None

        # 2. 상승률 체크
        if price_change_pct < min_price_change_pct:
            return None

        # 모든 조건 만족! 시그널 생성
        signal_info = {
            'symbol': symbol,
            'timestamp': pd.Timestamp.now(),
            'signal_type': 'STRONG_MOMENTUM',
            'quote_volume': quote_volume,
            'price_change_percent': price_change_pct,
        }

        # 알림 기록
        self.record_alert(symbol)

        logger.info(f"모멘텀 시그널 발생: {symbol} (상승률: {price_change_pct:+.2f}%)")

        return signal_info

    def get_signal_summary(self, signal_info: Dict) -> str:
        """
        시그널 정보 요약

        Args:
            signal_info: 시그널 정보

        Returns:
            요약 문자열
        """
        signal_type = signal_info.get('signal_type', '')
        symbol = signal_info['symbol']
        timestamp = signal_info['timestamp']

        # 한국시간(KST) 변환 (UTC + 9시간)
        if isinstance(timestamp, pd.Timestamp):
            kst_time = timestamp + timedelta(hours=9)
        else:
            kst_time = timestamp + timedelta(hours=9)

        # 시간 포맷팅
        time_str = kst_time.strftime('%Y-%m-%d %H:%M:%S KST')

        # 모멘텀 시그널
        if signal_type.startswith('STRONG_MOMENTUM'):
            price_change_pct = signal_info['price_change_percent']
            timeframe = signal_info.get('timeframe', '24h')

            emoji = "⚡💥"
            signal_msg = "강력한 모멘텀 감지"

            summary = f"""
{emoji} {signal_msg} {emoji}

심볼: {symbol}
{timeframe} 상승률: {price_change_pct:+.2f}%
시간: {time_str}
"""
            return summary.strip()

        # 역배열 시그널 (기존)
        else:
            price = signal_info['price']
            target_sma = signal_info['target_sma']
            target_sma_period = signal_info.get('target_sma_period', 480)

            # 시그널 메시지 (480만 사용, 1시간봉)
            signal_msg = f"역배열 & SMA480 근처 (±5%)"
            emoji = "🚀🎯"

            # 종가와 target SMA 차이 계산
            diff_pct = ((price - target_sma) / target_sma) * 100 if target_sma else 0

            summary = f"""
{emoji} {signal_msg} {emoji}

심볼: {symbol}
현재가: {price:.4f}
SMA480: {target_sma:.4f} (차이: {diff_pct:+.2f}%)
시간: {time_str}
"""
            return summary.strip()
