"""
SMA(단순이동평균) 계산 모듈
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class SMACalculator:
    """SMA 계산기"""

    def __init__(self, periods: List[int] = [120, 240, 480, 960]):
        """
        초기화

        Args:
            periods: SMA 기간 리스트
        """
        self.periods = sorted(periods)  # 오름차순 정렬
        self.max_period = max(periods)
        logger.info(f"SMA 계산기 초기화: 기간 {self.periods}")

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        단순이동평균 계산

        Args:
            df: OHLCV 데이터프레임
            period: 이동평균 기간

        Returns:
            SMA 시리즈
        """
        if df.empty or len(df) < period:
            logger.warning(f"데이터가 부족합니다. 필요: {period}, 현재: {len(df)}")
            return pd.Series()

        return df['close'].rolling(window=period).mean()

    def calculate_all_smas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 SMA 계산

        Args:
            df: OHLCV 데이터프레임

        Returns:
            SMA가 추가된 데이터프레임
        """
        if df.empty:
            return df

        df_result = df.copy()

        for period in self.periods:
            col_name = f'sma_{period}'
            df_result[col_name] = self.calculate_sma(df, period)

        return df_result

    def check_reverse_alignment(self, sma_values: Dict[int, float]) -> bool:
        """
        역배열 확인 (긴 기간 SMA가 짧은 기간 SMA보다 위에 있는지)

        Args:
            sma_values: {기간: SMA값} 딕셔너리

        Returns:
            역배열 여부
        """
        if not sma_values or len(sma_values) != len(self.periods):
            return False

        # NaN 체크
        for period in self.periods:
            if period not in sma_values or pd.isna(sma_values[period]):
                return False

        # 역배열 확인: SMA960 > SMA480 > SMA240 > SMA120
        sorted_periods = sorted(self.periods)
        for i in range(len(sorted_periods) - 1):
            current_period = sorted_periods[i]
            next_period = sorted_periods[i + 1]

            if sma_values[current_period] >= sma_values[next_period]:
                return False

        return True

    def get_current_sma_values(self, df: pd.DataFrame) -> Dict[int, float]:
        """
        현재(최신) SMA 값들 가져오기

        Args:
            df: SMA가 계산된 데이터프레임

        Returns:
            {기간: SMA값} 딕셔너리
        """
        if df.empty:
            return {}

        sma_values = {}
        for period in self.periods:
            col_name = f'sma_{period}'
            if col_name in df.columns:
                sma_values[period] = df[col_name].iloc[-1]

        return sma_values

    def get_sma_alignment_score(self, sma_values: Dict[int, float]) -> float:
        """
        SMA 정렬 점수 계산 (0-100)
        100 = 완벽한 역배열, 0 = 정배열 또는 뒤섞임

        Args:
            sma_values: {기간: SMA값} 딕셔너리

        Returns:
            정렬 점수
        """
        if not sma_values or len(sma_values) != len(self.periods):
            return 0.0

        sorted_periods = sorted(self.periods)
        score = 0
        max_score = len(sorted_periods) - 1

        for i in range(len(sorted_periods) - 1):
            current_period = sorted_periods[i]
            next_period = sorted_periods[i + 1]

            if pd.isna(sma_values.get(current_period)) or pd.isna(sma_values.get(next_period)):
                continue

            # 짧은 기간이 긴 기간보다 아래에 있으면 점수 획득 (역배열)
            if sma_values[current_period] < sma_values[next_period]:
                score += 1

        return (score / max_score * 100) if max_score > 0 else 0.0

    def format_sma_values(self, sma_values: Dict[int, float]) -> str:
        """
        SMA 값들을 보기 좋게 포맷팅

        Args:
            sma_values: {기간: SMA값} 딕셔너리

        Returns:
            포맷팅된 문자열
        """
        if not sma_values:
            return "N/A"

        parts = []
        for period in sorted(self.periods):
            if period in sma_values:
                value = sma_values[period]
                if pd.isna(value):
                    parts.append(f"SMA{period}: N/A")
                else:
                    parts.append(f"SMA{period}: {value:.4f}")

        return " | ".join(parts)
