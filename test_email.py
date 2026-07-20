import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("SMTP_EMAIL")
PASSWORD = os.getenv("SMTP_PASSWORD")

print("Email:", EMAIL)
print("Password length:", len(PASSWORD))

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    print("✅ LOGIN SUCCESS")
    server.quit()
except Exception as e:
    print("❌ LOGIN FAILED")
    print(e)