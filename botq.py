import os

email=os.getenv("REMANGA_EMAIL"),
password=os.getenv("REMANGA_PASSWORD"),
telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
chat_id=os.getenv("TELEGRAM_CHAT_ID"),
proxy=os.getenv("CUSTOM_PROXY"),
with open("m.txt","w+") as f:
    f.write(f"{email}\n")
    f.write(f"{password}\n")
    f.write(f"{telegram_token}\n")
    f.write(f"{chat_id}\n")
    f.write(f"{proxy}\n")
