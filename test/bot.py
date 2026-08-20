import time
import random
import schedule
import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth 
import requests

def send_telegram_message(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
    except: pass

def human_sleep(min_sec=2, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def get_file_path(filename):
    """Возвращает правильный путь к файлу (cookies.txt или proxies.json)"""
    if 'GITHUB_WORKSPACE' in os.environ:
        return str(Path(os.environ['GITHUB_WORKSPACE']) / 'test' / filename)
    return str(Path(__file__).parent / filename)

def parse_netscape_cookies(file_path):
    cookies = []
    if not os.path.exists(file_path): return cookies
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split("\t")
            if len(parts) >= 7:
                domain, flag, path, secure, expiration, name, value = parts[:7]
                cookie = {
                    "name": name, "value": value, "domain": domain, "path": path,
                    "secure": secure.upper() == "TRUE", "httpOnly": False,
                    "expires": int(expiration) if expiration.isdigit() else None
                }
                cookie = {k: v for k, v in cookie.items() if v is not None}
                cookies.append(cookie)
    return cookies

def setup_browser_with_proxy(p, is_github):
    """Умный запуск браузера с перебором прокси (если нужно)"""
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # ЕСЛИ ЗАПУСК ЛОКАЛЬНЫЙ (НА ПК) - ПРОКСИ НЕ НУЖНЫ
    if not is_github:
        print("💻 Локальный запуск: прокси отключены, браузер видимый.")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
        return browser, context, context.new_page()

    # ЕСЛИ ЗАПУСК НА GITHUB - ИЩЕМ РАБОЧИЙ ПРОКСИ
    print("☁️ Запуск на GitHub: начинаю перебор прокси...")
    proxies_path = get_file_path('proxies.json')
    
    if not os.path.exists(proxies_path):
        print("❌ Файл proxies.json не найден! Запускаю без прокси (скорее всего будет ошибка 403).")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
        return browser, context, context.new_page()

    # Загружаем и перемешиваем прокси
    with open(proxies_path, 'r') as f:
        proxies_list = json.load(f)
    random.shuffle(proxies_list)
    print(f"🔍 Загружено прокси для проверки: {len(proxies_list)}")

    # Начинаем перебор
    for proxy_data in proxies_list:
        proxy_server = f"http://{proxy_data['ip_address']}:{proxy_data['port']}"
        print(f"\n🔄 Тестирую прокси: {proxy_server}")
        
        try:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": proxy_server}
            )
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
            page = context.new_page()
            
            # Применяем анти-детект
            stealth = Stealth()
            stealth.apply_stealth_sync(page)

            # Пытаемся зайти на сайт (даем прокси максимум 15 секунд на ответ)
            response = page.goto("https://реманга.орг/murim-cards#/map", timeout=15000, wait_until="domcontentloaded")
            
            # Проверяем, не выдал ли сайт 403 ошибку
            if response and response.status in [403, 502, 503, 504]:
                print(f"❌ Прокси заблокирован сайтом (Статус: {response.status}). Ищу другой...")
                browser.close()
                continue
            
            # Проверяем текст на странице на случай хитрой блокировки
            if page.locator('text="403"').is_visible(timeout=3000):
                print(f"❌ Прокси выдал страницу 403 (VPN/СНГ блок). Ищу другой...")
                browser.close()
                continue

            print(f"✅ ОТЛИЧНО! Найден рабочий прокси: {proxy_server}")
            return browser, context, page

        except Exception as e:
            print(f"❌ Прокси не отвечает (Таймаут/Мертвый). Ищу другой...")
            try: browser.close()
            except: pass

    print("🚨 ВСЕ ПРОКСИ ИЗ СПИСКА НЕ РАБОТАЮТ ИЛИ ЗАБЛОКИРОВАНЫ.")
    return None, None, None

def run_dungeon_bot():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] Запуск задачи фарма катакомб...")
    
    is_github = 'GITHUB_ACTIONS' in os.environ
    
    with sync_playwright() as p:
        browser, context, page = setup_browser_with_proxy(p, is_github)
        
        if not browser:
            send_telegram_message("❌ Бот остановлен: не удалось найти рабочий прокси.")
            return

        try:
            # Загружаем куки (если есть) в рабочий контекст
            cookies_path = get_file_path('cookies.txt')
            netscape_cookies = parse_netscape_cookies(cookies_path)
            if netscape_cookies:
                context.add_cookies(netscape_cookies)
                # Перезагружаем страницу с куками
                page.goto("https://реманга.орг/murim-cards#/map", timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Ошибка загрузки куки: {e}")

        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        try:
            human_sleep(3, 5)
            
            # ==========================================
            # АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ
            # ==========================================
            try:
                login_btn = page.locator('text="Войти"').first
                if login_btn.is_visible(timeout=5000):
                    print("⚠️ Куки не сработали. Начинаю автоматический вход...")
                    login_btn.click()
                    human_sleep(2, 3)
                    
                    email_field = page.locator('input[type="text"], input[type="email"], input[name="username"]').first
                    email_field.fill("zavlatkamalov@gmail.com")
                    human_sleep(1, 2)
                    
                    pass_field = page.locator('input[type="password"]').first
                    pass_field.fill("Zafarjon1224")
                    human_sleep(1, 2)
                    
                    submit_btn = page.locator('button[type="submit"], button:has-text("Войти")').last
                    submit_btn.click()
                    
                    print("✅ Данные отправлены. Жду прогрузки аккаунта...")
                    human_sleep(6, 8)
                    page.goto("https://реманга.орг/murim-cards#/map", timeout=60000, wait_until="domcontentloaded")
                    human_sleep(5, 7)
            except Exception as login_err:
                print("Окно входа не найдено. Похоже, мы уже авторизованы.")
            # ==========================================

            page.screenshot(path="error_screenshot.png")
            print("📸 Сделан контрольный скриншот.")
            
        except Exception as e:
            print(f"❌ Ошибка на этапе загрузки/входа: {e}")
            browser.close()
            return
        
        # Закрываем всплывающую рекламу
        try:
            close_btn = page.locator('button[aria-label="Закрыть"]')
            if close_btn.is_visible(timeout=5000):
                close_btn.click()
                human_sleep(2, 3)
        except: pass

        run_count = 1
        
        while True:
            try:
                print(f"\n--- Запуск цикла прохода №{run_count} ---")
                
                kanji_element = page.locator('span.font-kanji', has_text='寺')
                kanji_element.first.wait_for(state="visible", timeout=20000)
                
                if kanji_element.count() > 0:
                    kanji_element.first.click()
                    print("✅ Кликнул по иероглифу 寺!")
                else:
                    print("Иероглиф 寺 не найден. Возможно, закончилась энергия или сбой карты.")
                    break 
                
                human_sleep(2, 3)

                pass_button = page.locator('text=ПРОЙТИ СНОВА')
                try:
                    pass_button.wait_for(state="visible", timeout=5000)
                    is_disabled = pass_button.evaluate("node => node.disabled || node.getAttribute('aria-disabled') === 'true'")
                    if is_disabled:
                        print("Энергия закончилась! Кнопка заблокирована.")
                        break
                    pass_button.click()
                except Exception as ex:
                    print(f"Кнопка 'ПРОЙТИ СНОВА' недоступна: {ex}")
                    break
                
                human_sleep(2, 3)

                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                print("Жду завершения боя...")
                human_sleep(12, 16)

                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except: break
                
                human_sleep(2, 3)

                try:
                    page.locator('button[data-sentry-source-file="pve-result-overlay.tsx"]').click(timeout=8000)
                    print("✅ Возвращаемся на карту.")
                except: break
                
                run_count += 1
                human_sleep(4, 6)
                
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                try: page.screenshot(path="error_screenshot.png")
                except: pass
                break

        print("Фарм завершен. Закрываю браузер.")
        browser.close()

if __name__ == "__main__":
    run_dungeon_bot()
