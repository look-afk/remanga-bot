import os
import requests

email = os.getenv("REMANGA_EMAIL")
password = os.getenv("REMANGA_PASSWORD")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
proxy = os.getenv("CUSTOM_PROXY")

print("EMAIL:", email)
print("PASSWORD:", "установлен" if password else "не установлен")
print("TELEGRAM TOKEN:", "установлен" if telegram_token else "не установлен")
print("CHAT ID:", chat_id)
print("PROXY:", "установлен" if proxy else "не установлен")
