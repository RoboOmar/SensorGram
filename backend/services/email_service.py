import requests
import traceback
from backend.config import settings

def send_test_email(email_to: str):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": email_to,
                "subject": "Sensorgram - Test Email",
                "html": "<p>This is a test email sent via Resend API from the live server.</p>"
            }
        )
        if response.status_code in [200, 201, 202]:
            print(f"Email sent successfully to {email_to}")
            return True
        else:
            print(f"Resend API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Failed to send email to {email_to}:")
        traceback.print_exc()
        return False

def send_reset_email(email_to: str, token: str):
    reset_link = f"https://sensorgram.onrender.com/reset-password?token={token}"
    print(f"Attempting to send email to... {email_to}")
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": email_to,
                "subject": "Password Reset Request",
                "html": f"<p>Click the link to reset your password:</p><p><a href='{reset_link}'>{reset_link}</a></p>"
            }
        )
        if response.status_code in [200, 201, 202]:
            print(f"Password reset email sent to {email_to}")
            return True
        else:
            print(f"Resend API Error: {response.status_code} - {response.text}")
            print("\n" + "=" * 40)
            print("FALLBACK PASSWORD RESET LINK:")
            print(reset_link)
            print("=" * 40 + "\n")
            return False
    except Exception as e:
        print(f"Exception while sending password reset email to {email_to}:")
        traceback.print_exc()
        print("\n" + "=" * 40)
        print("FALLBACK PASSWORD RESET LINK:")
        print(reset_link)
        print("=" * 40 + "\n")
        return False
