"""
알림 모듈
콘솔, 텔레그램, 디스코드, 이메일 알림 지원
"""
import logging
from typing import Dict, List
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """알림 전송기"""

    def __init__(self, config: Dict):
        """
        초기화

        Args:
            config: 알림 설정 딕셔너리
        """
        self.config = config
        self.methods = config.get('METHODS', {})

        # 활성화된 알림 방법 확인
        self.console_enabled = self.methods.get('CONSOLE', True)
        self.telegram_enabled = self.methods.get('TELEGRAM', False)
        self.discord_enabled = self.methods.get('DISCORD', False)
        self.email_enabled = self.methods.get('EMAIL', False)

        # 텔레그램 설정
        if self.telegram_enabled:
            telegram_config = config.get('TELEGRAM', {})
            self.telegram_bot_token = telegram_config.get('BOT_TOKEN', '')
            self.telegram_chat_id = telegram_config.get('CHAT_ID', '')

            if not self.telegram_bot_token or not self.telegram_chat_id:
                logger.warning("텔레그램 설정이 불완전합니다. 텔레그램 알림이 비활성화됩니다.")
                self.telegram_enabled = False

        # 디스코드 설정
        if self.discord_enabled:
            discord_config = config.get('DISCORD', {})
            self.discord_webhook_url = discord_config.get('WEBHOOK_URL', '')

            if not self.discord_webhook_url:
                logger.warning("디스코드 웹훅 URL이 없습니다. 디스코드 알림이 비활성화됩니다.")
                self.discord_enabled = False

        enabled_methods = [m for m, enabled in self.methods.items() if enabled]
        logger.info(f"알림 방법 활성화: {', '.join(enabled_methods)}")

    def send_console(self, message: str):
        """콘솔에 메시지 출력"""
        if not self.console_enabled:
            return

        print("\n" + "=" * 60)
        print(message)
        print("=" * 60 + "\n")

    def send_telegram(self, message: str):
        """텔레그램으로 메시지 전송"""
        if not self.telegram_enabled:
            return

        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            logger.info("텔레그램 알림 전송 성공")

        except Exception as e:
            logger.error(f"텔레그램 알림 전송 실패: {e}")

    def send_discord(self, message: str):
        """디스코드로 메시지 전송"""
        if not self.discord_enabled:
            return

        try:
            data = {
                'content': message
            }

            response = requests.post(self.discord_webhook_url, json=data, timeout=10)
            response.raise_for_status()

            logger.info("디스코드 알림 전송 성공")

        except Exception as e:
            logger.error(f"디스코드 알림 전송 실패: {e}")

    def send_email(self, subject: str, message: str):
        """이메일로 메시지 전송"""
        if not self.email_enabled:
            return

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            email_config = self.config.get('EMAIL', {})
            smtp_server = email_config.get('SMTP_SERVER')
            smtp_port = email_config.get('SMTP_PORT')
            sender = email_config.get('SENDER_EMAIL')
            password = email_config.get('SENDER_PASSWORD')
            receiver = email_config.get('RECEIVER_EMAIL')

            if not all([smtp_server, smtp_port, sender, password, receiver]):
                logger.warning("이메일 설정이 불완전합니다.")
                return

            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)

            logger.info("이메일 알림 전송 성공")

        except Exception as e:
            logger.error(f"이메일 알림 전송 실패: {e}")

    def send_signal_alert(self, signal_info: Dict, summary: str):
        """
        시그널 알림 전송

        Args:
            signal_info: 시그널 정보
            summary: 시그널 요약 메시지
        """
        symbol = signal_info['symbol']
        price = signal_info['price']

        # 콘솔 출력
        self.send_console(summary)

        # 텔레그램 (HTML 포맷)
        if self.telegram_enabled:
            signal_type = signal_info.get('signal_type', 'UNKNOWN')
            reverse_aligned = signal_info.get('reverse_aligned', False)
            near_target = signal_info.get('near_target', False)
            target_sma = signal_info['target_sma']
            target_sma_period = signal_info.get('target_sma_period', 960)

            # 시그널 메시지
            if target_sma_period == 960:
                emoji = "🚀🎯"
                msg_title = f"역배열 & SMA{target_sma_period} 근처 (±5%)"
            else:  # 480
                emoji = "⚡🎯"
                msg_title = f"역배열 & SMA{target_sma_period} 근처 (±5%)"

            # 차이 계산
            diff_pct = ((price - target_sma) / target_sma) * 100 if target_sma else 0

            telegram_msg = f"""
<b>{emoji} {msg_title} {emoji}</b>

<b>심볼:</b> {symbol}
<b>현재가:</b> {price:.4f}
<b>SMA{target_sma_period}:</b> {target_sma:.4f} (차이: {diff_pct:+.2f}%)
<b>시간:</b> {signal_info['timestamp']}

<b>SMA 정렬:</b>
{self._format_sma_values_html(signal_info['sma_values'], target_sma_period)}

<b>상태:</b>
- 역배열: {'✅' if reverse_aligned else '❌'}
- SMA{target_sma_period} 근처: {'✅' if near_target else '❌'}
"""
            self.send_telegram(telegram_msg.strip())

        # 디스코드
        if self.discord_enabled:
            self.send_discord(summary)

        # 이메일
        if self.email_enabled:
            subject = f"[Binance Alert] {symbol} SMA960 돌파!"
            self.send_email(subject, summary)

    def send_system_message(self, message: str, level: str = "INFO"):
        """
        시스템 메시지 전송

        Args:
            message: 메시지
            level: 로그 레벨 (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"

        # 콘솔은 항상 출력
        print(formatted_msg)

        # 에러는 텔레그램으로도 전송
        if level == "ERROR" and self.telegram_enabled:
            self.send_telegram(f"⚠️ <b>시스템 에러</b>\n\n{message}")

    def _format_sma_values_html(self, sma_values: Dict[int, float], target_sma_period: int = 960) -> str:
        """SMA 값들을 HTML 포맷으로 변환"""
        parts = []
        # target_sma_period에 따라 표시할 SMA 결정
        if target_sma_period == 960:
            display_periods = [960, 480, 240, 120]
        else:  # 480
            display_periods = [480, 240, 120]

        for period in display_periods:
            if period in sma_values:
                value = sma_values[period]
                parts.append(f"SMA{period}: {value:.4f}")
        return "\n".join(parts)

    def test_notifications(self):
        """알림 테스트"""
        test_message = "🔔 바이낸스 SMA 모니터 알림 테스트"

        logger.info("알림 테스트 시작...")

        if self.console_enabled:
            self.send_console(test_message)
            logger.info("✓ 콘솔 알림 테스트 완료")

        if self.telegram_enabled:
            self.send_telegram(test_message)
            logger.info("✓ 텔레그램 알림 테스트 완료")

        if self.discord_enabled:
            self.send_discord(test_message)
            logger.info("✓ 디스코드 알림 테스트 완료")

        if self.email_enabled:
            self.send_email("알림 테스트", test_message)
            logger.info("✓ 이메일 알림 테스트 완료")

        logger.info("알림 테스트 완료!")
