"""
Простой Telegram бот для управления ботом фарма
Запускается локально на компьютере
"""

import os
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_message(text):
    """Отправляет сообщение в Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Ошибка: не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def get_updates(offset=0):
    """Получает обновления от Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return {"ok": False}

def handle_message(message):
    """Обрабатывает входящие сообщения"""
    text = message.get('text', '').lower()
    chat_id = message['chat']['id']
    
    if text == '/start':
        response_text = (
            "🤖 Привет! Я бот фарма Remanga\n\n"
            "Доступные команды:\n"
            "/status - статус бота\n"
            "/help - справка\n\n"
            "Бот автоматически запускается каждый день в 10:00 UTC "
            "на GitHub Actions и отправляет мне отчет о работе в Telegram 📊"
        )
        send_message(response_text)
    
    elif text == '/status':
        response_text = "✅ Бот онлайн и работает!\n\nСледующий запуск: каждый день в 10:00 UTC"
        send_message(response_text)
    
    elif text == '/help':
        response_text = (
            "📖 Справка:\n\n"
            "/start - приветствие\n"
            "/status - статус\n"
            "/help - эта справка\n\n"
            "Все логи смотри в GitHub Actions:\n"
            "https://github.com/look-afk/remanga-bot/actions"
        )
        send_message(response_text)

def main():
    """Основной цикл бота"""
    print("🤖 Telegram бот запущен!")
    print(f"Токен: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    print("Слушаю сообщения... (Ctrl+C для выхода)\n")
    
    offset = 0
    
    try:
        while True:
            result = get_updates(offset)
            
            if result.get('ok'):
                updates = result.get('result', [])
                
                for update in updates:
                    offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        message = update['message']
                        print(f"📨 Сообщение: {message.get('text', '[нет текста]')}")
                        handle_message(message)
            
            # Небольшая задержка, чтобы не перегружать API
            import time
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Ошибка: переменные окружения не установлены!")
        print("\nЧтобы запустить бота, создай файл .env в текущей папке:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен")
        print("TELEGRAM_CHAT_ID=ваш_chat_id")
    else:
        main()
