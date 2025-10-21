#!/usr/bin/env python3
"""
텔레그램 설정 테스트 스크립트
"""
import requests
import sys

def test_telegram(bot_token, chat_id=None):
    """텔레그램 봇 테스트"""

    print("=" * 60)
    print("텔레그램 봇 테스트")
    print("=" * 60)

    # 1. 봇 정보 확인
    print("\n[1단계] 봇 정보 확인 중...")
    url = f"https://api.telegram.org/bot{bot_token}/getMe"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ 봇 연결 성공!")
            print(f"   봇 이름: {bot_info.get('first_name')}")
            print(f"   봇 유저네임: @{bot_info.get('username')}")
            print(f"   봇 ID: {bot_info.get('id')}")
        else:
            print(f"❌ 봇 연결 실패!")
            print(f"   에러: {data.get('description')}")
            print(f"\n💡 해결방법:")
            print(f"   1. BOT_TOKEN이 정확한지 확인")
            print(f"   2. @BotFather에서 /mybots → 본인 봇 → API Token 확인")
            return False
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return False

    # 2. 최근 업데이트 확인 (Chat ID 찾기)
    print("\n[2단계] Chat ID 확인 중...")
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('ok'):
            updates = data.get('result', [])

            if not updates:
                print("⚠️  최근 메시지가 없습니다!")
                print("\n💡 해결방법:")
                print(f"   1. 텔레그램에서 @{bot_info.get('username')} 봇 검색")
                print(f"   2. START 버튼 클릭")
                print(f"   3. 아무 메시지나 보내기 (예: '테스트')")
                print(f"   4. 이 스크립트 다시 실행")
                return False

            print(f"✅ {len(updates)}개의 업데이트 발견!")

            # 모든 고유한 Chat ID 추출
            chat_ids = set()
            for update in updates:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    chat_type = update['message']['chat']['type']
                    chat_ids.add((chat_id, chat_type))

            print("\n발견된 Chat ID:")
            for idx, (cid, ctype) in enumerate(chat_ids, 1):
                print(f"   {idx}. Chat ID: {cid} (타입: {ctype})")

            if len(chat_ids) == 1:
                detected_chat_id = list(chat_ids)[0][0]
                print(f"\n📝 사용할 Chat ID: {detected_chat_id}")

                # 3. 테스트 메시지 보내기
                if chat_id:
                    if str(chat_id) != str(detected_chat_id):
                        print(f"\n⚠️  입력한 Chat ID ({chat_id})가 실제 Chat ID ({detected_chat_id})와 다릅니다!")
                        chat_id = detected_chat_id
                else:
                    chat_id = detected_chat_id

                print(f"\n[3단계] 테스트 메시지 전송 중... (Chat ID: {chat_id})")

                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': '🔔 텔레그램 연결 테스트 성공!\n\n바이낸스 SMA 모니터가 정상적으로 작동합니다.',
                    'parse_mode': 'HTML'
                }

                response = requests.post(url, data=payload, timeout=10)
                data = response.json()

                if data.get('ok'):
                    print("✅ 테스트 메시지 전송 성공!")
                    print("\n" + "=" * 60)
                    print("GitHub Secrets에 다음 값을 입력하세요:")
                    print("=" * 60)
                    print(f"TELEGRAM_BOT_TOKEN: {bot_token}")
                    print(f"TELEGRAM_CHAT_ID: {chat_id}")
                    print("=" * 60)
                    return True
                else:
                    print(f"❌ 메시지 전송 실패: {data.get('description')}")
                    return False
            else:
                print("\n⚠️  여러 개의 Chat ID가 발견되었습니다.")
                print("   Chat ID를 직접 입력해서 다시 실행해주세요.")
                return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("\n텔레그램 봇 설정 테스트 도구\n")

    if len(sys.argv) < 2:
        print("사용법:")
        print(f"  python3 {sys.argv[0]} <BOT_TOKEN>")
        print(f"  python3 {sys.argv[0]} <BOT_TOKEN> <CHAT_ID>")
        print("\n예시:")
        print(f"  python3 {sys.argv[0]} 123456:ABC-DEF1234")
        sys.exit(1)

    bot_token = sys.argv[1]
    chat_id = sys.argv[2] if len(sys.argv) > 2 else None

    success = test_telegram(bot_token, chat_id)

    if not success:
        sys.exit(1)
