async def send_test_email(email_to: str):
    print("=" * 40)
    print("MOCK EMAIL SENT:")
    print(f"To: {email_to}")
    print("Subject: Sensorgram - Test Email")
    print("Body: This is a test email sent via mocked print statement to bypass all network configurations.")
    print("=" * 40)
    # The API route already handles returning the 200 success response, we just return here.
    return True

async def send_reset_email(email_to: str, token: str):
    reset_link = f"http://localhost:8000/reset-password?token={token}"
    print("=" * 40)
    print("MOCK EMAIL SENT:")
    print(f"To: {email_to}")
    print("Subject: Sensorgram - Password Reset")
    print(f"Body: Click the link to reset your password: {reset_link}")
    print("=" * 40)
    return True
