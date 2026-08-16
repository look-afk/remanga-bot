import time
import random
import schedule
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return  # Если нет токена/chat_id, пропускаем
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def human_sleep(min_sec=2, max_sec=4):
    """Случайная пауза для имитации человека"""
    time.sleep(random.uniform(min_sec, max_sec))

def get_cookies_path():
    """Возвращает путь к cookies.txt, работает как локально, так и на GitHub Actions"""
    # Сначала проверяем переменную окружения (для GitHub Actions)
    if 'GITHUB_WORKSPACE' in os.environ:
        cookies_path = Path(os.environ['GITHUB_WORKSPACE']) / 'test' / 'cookies.txt'
    else:
        # Локальный путь (относительно места запуска скрипта)
        cookies_path = Path(__file__).parent / 'cookies.txt'
    
    return str(cookies_path)

def parse_netscape_cookies(file_path):
    """Конвертирует Netscape cookies.txt в формат Playwright"""
    cookies = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split("\t")
            if len(parts) >= 7:
                domain, flag, path, secure, expiration, name, value = parts[:7]
                
                cookie = {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": path,
                    "secure": secure.upper() == "TRUE",
                    "httpOnly": False,
                    "expires": int(expiration) if expiration.isdigit() else None
                }
                cookie = {k: v for k, v in cookie.items() if v is not None}
                cookies.append(cookie)
    return cookies

def run_dungeon_bot():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] Запуск запланированной задачи фарма катакомб...")
    send_telegram_message(f"🤖 Бот начал работу! ⏰ {timestamp}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # На сервере можно поставить True (без графического окна)
        context = browser.new_context()

        # Загружаем куки (работает как локально, так и на GitHub Actions)
        try:
            cookies_path = get_cookies_path()
            netscape_cookies = parse_netscape_cookies(cookies_path)
            context.add_cookies(netscape_cookies)
        except Exception as e:
            error_msg = f"❌ Ошибка при загрузке cookies.txt: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
            browser.close()
            return

        page = context.new_page()

        try:
            page.goto("https://remanga.org/murim-cards#/map", timeout=60000)
            human_sleep(5, 7)
        except Exception as e:
            print(f"Не удалось открыть страницу: {e}")
            browser.close()
            return
        
        # Закрываем промо-окно, если есть
        try:
            promo_close_btn = page.locator('button[aria-label="Закрыть промо подписки"]')
            if promo_close_btn.is_visible(timeout=3000):
                promo_close_btn.click()
                human_sleep(1, 2)
        except:
            pass

        run_count = 1
        
        while True:
            try:
                print(f"--- Запуск цикла прохода №{run_count} ---")
                
                page.wait_for_selector('div[data-sentry-component="MarkerPin"]', timeout=10000)
                markers = page.locator('div[data-sentry-component="MarkerPin"]')
                
                if markers.count() > 3:
                    markers.nth(3).click()
                else:
                    print("Маркеры на карте не найдены.")
                    break 
                
                human_sleep(2, 3)

                pass_button = page.locator('text=ПРОЙТИ СНОВА')
                try:
                    pass_button.wait_for(state="visible", timeout=5000)
                    is_disabled = pass_button.evaluate("node => node.disabled || node.getAttribute('aria-disabled') === 'true'")
                    if is_disabled:
                        print("Энергия закончилась! Кнопка прохода заблокирована.")
                        break
                    pass_button.click()
                except Exception as ex:
                    print(f"Энергия исчерпана или кнопка недоступна: {ex}")
                    break
                
                print("Жду завершения боя...")
                human_sleep(10, 15)

                try:
                    page.locator('text=К результатам').click(timeout=5000)
                except:
                    break
                
                human_sleep(2, 3)

                try:
                    page.locator('button[data-sentry-source-file="pve-result-overlay.tsx"]').click(timeout=5000)
                except:
                    break
                
                run_count += 1
                human_sleep(3, 5)
                
            except Exception as e:
                print(f"Ошибка в цикле: {e}")
                break

        print("Фарм завершен. Закрываю браузер.")
        browser.close()
        send_telegram_message(f"✅ Фарм завершен! Циклов: {run_count}")

def schedule_job():
    """Выбирает случайный час из [13, 14, 15] и ставит задачу на этот час"""
    chosen_hour = random.choice([13, 14, 15])
    # Форматируем время в строку вида "13:00", "14:00" или "15:00"
    time_str = f"{chosen_hour:02d}:00"
    
    print(f"Сегодня бот запустится в обед в {time_str}")
    
    # Очищаем старые задачи и назначаем новую на сегодня
    schedule.clear()
    schedule.every().day.at(time_str).do(job_wrapper)

def job_wrapper():
    run_dungeon_bot()
    # После выполнения переназначаем время на следующий день
    schedule_job()

if __name__ == "__main__":
    # На GitHub Actions запускаем один раз и выходим
    if 'GITHUB_ACTIONS' in os.environ:
        print("[GitHub Actions] Запуск бота один раз...")
        run_dungeon_bot()
    else:
        # Локально - используем планировщик
        print("Бот-планировщик запущен и ждет обеденного времени...")
        schedule_job()

        # Бесконечный цикл проверки расписания
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяю каждую минуту, настало ли время