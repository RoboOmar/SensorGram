import smtplib
from email.message import EmailMessage
from backend.config import settings

def send_test_email(email_to: str):
    msg = EmailMessage()
    msg.set_content("This is a test email sent via SMTP from the live server.")
    msg["Subject"] = "Sensorgram - Test Email"
    msg["From"] = settings.MAIL_FROM
    msg["To"] = email_to

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent successfully to {email_to}")
        return True
    except Exception as e:
        print(f"Failed to send email to {email_to}: {e}")
        return False

def send_reset_email(email_to: str, token: str):
    reset_link = f"https://sensorgram.onrender.com/reset-password?token={token}"
    msg = EmailMessage()
    msg.set_content(f"Click the link to reset your password:\n{reset_link}")
    msg["Subject"] = "Sensorgram - Password Reset"
    msg["From"] = settings.MAIL_FROM
    msg["To"] = email_to

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
        print(f"Password reset email sent to {email_to}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {email_to}: {e}")
        return False
