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

    def __init__(self, target_sma: int = 960, confirm_candles: int = 1, cooldown: int = 3600):
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

    def check_near_sma960(self, df: pd.DataFrame, tolerance_pct: float = 5.0) -> bool:
        """
        종가가 SMA960의 ±tolerance_pct% 이내인지 확인

        Args:
            df: SMA가 계산된 데이터프레임
            tolerance_pct: 허용 오차 퍼센트 (기본 5%)

        Returns:
            SMA960 근처 여부
        """
        if df.empty or self.target_sma_col not in df.columns:
            return False

        # 현재 캔들
        current_candle = df.iloc[-1]
        current_close = current_candle['close']
        current_sma = current_candle[self.target_sma_col]

        # NaN 체크
        if pd.isna(current_close) or pd.isna(current_sma):
            return False

        # 종가가 SMA960의 ±tolerance_pct% 이내인지 확인
        lower_bound = current_sma * (1 - tolerance_pct / 100)
        upper_bound = current_sma * (1 + tolerance_pct / 100)

        is_near = lower_bound <= current_close <= upper_bound

        if is_near:
            diff_pct = ((current_close - current_sma) / current_sma) * 100
            # 심볼 정보는 analyze_signal에서 전달받을 것이므로 여기서는 로그 제거

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
                      reverse_aligned: bool, breakout_type: str = "CLOSE") -> Optional[Dict]:
        """
        종합 시그널 분석

        Args:
            symbol: 심볼
            df: SMA가 계산된 데이터프레임
            sma_values: 현재 SMA 값들
            reverse_aligned: 역배열 여부
            breakout_type: 돌파 타입 (CLOSE, BODY, NEAR)

        Returns:
            시그널 정보 딕셔너리 (시그널 없으면 None)
        """
        # SMA960 근처 확인
        near_sma960 = self.check_near_sma960(df, tolerance_pct=5.0)

        # 조건: 역배열 AND SMA960 근처
        if not (reverse_aligned and near_sma960):
            return None

        # 쿨다운 확인
        if not self.should_send_alert(symbol):
            return None

        # 현재 캔들 정보
        current_candle = df.iloc[-1]
        current_price = current_candle['close']
        current_time = df.index[-1]

        # 시그널 타입 (항상 역배열 AND SMA960 근처)
        signal_type = "REVERSE_ALIGNED_AND_NEAR"

        # 시그널 정보 생성
        signal_info = {
            'symbol': symbol,
            'timestamp': current_time,
            'price': current_price,
            'sma_values': sma_values,
            'target_sma': sma_values.get(self.target_sma),
            'signal_type': signal_type,
            'reverse_aligned': reverse_aligned,
            'near_sma960': near_sma960,
        }

        # 알림 기록
        self.record_alert(symbol)

        logger.info(f"시그널 발생: {symbol} @ {current_price:.4f} (타입: {signal_type})")

        return signal_info

    def get_signal_summary(self, signal_info: Dict) -> str:
        """
        시그널 정보 요약

        Args:
            signal_info: 시그널 정보

        Returns:
            요약 문자열
        """
        symbol = signal_info['symbol']
        price = signal_info['price']
        target_sma = signal_info['target_sma']
        timestamp = signal_info['timestamp']

        # 시그널 메시지 (항상 역배열 AND SMA960 근처)
        signal_msg = "역배열 & SMA960 근처 (±5%)"
        emoji = "🚀🎯"

        # 종가와 SMA960 차이 계산
        diff_pct = ((price - target_sma) / target_sma) * 100 if target_sma else 0

        summary = f"""
{emoji} {signal_msg} {emoji}

심볼: {symbol}
현재가: {price:.4f}
SMA960: {target_sma:.4f} (차이: {diff_pct:+.2f}%)
시간: {timestamp}
"""
        return summary.strip()
