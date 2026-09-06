import os
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My Variables</title>
</head>
<body>
    <h1>Привет!</h1>

    <p><b>Email:</b> {{ email }}</p>
    <p><b>Password:</b> {{ password }}</p>
    <p><b>Telegram Token:</b> {{ telegram_token }}</p>
    <p><b>Chat ID:</b> {{ chat_id }}</p>
    <p><b>Proxy:</b> {{ proxy }}</p>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML,
        email=os.getenv("REMANGA_EMAIL"),
        password=os.getenv("REMANGA_PASSWORD"),
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        proxy=os.getenv("CUSTOM_PROXY"),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
