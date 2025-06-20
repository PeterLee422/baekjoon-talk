# app/services/email.py

def send_reset_email(
        email: str,
        token: str
) -> None:
    """
    모의 비밀번호 재설정 이메일 발송 함수
    """
    print(f"[MOCK EMAIL] 비밀번호 재설정 링크: http://localhost:8000/reset?token={token} (받는 사람: {email})")