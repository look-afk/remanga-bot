import time
import random
import schedule
import os
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth 
import requests

TARGET_URL = "https://remanga.org/murim-cards#/map"

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

def fetch_free_cis_proxies():
    """Автоматический бесплатный сбор свежих СНГ прокси (RU, KZ, BY) из открытых источников"""
    proxies = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Geonode API (RU/KZ/BY)
    try:
        url = 'https://proxylist.geonode.com/api/proxy-list?country=RU&limit=40&page=1&sort_by=lastChecked&sort_type=desc'
        res = requests.get(url, timeout=5, headers=headers)
        if res.status_code == 200:
            for item in res.json().get('data', []):
                proto = item.get('protocols', ['http'])[0].lower()
                ip = item.get('ip')
                port = item.get('port')
                if proto in ['http', 'https', 'socks5', 'socks4']:
                    proxies.append(f"{proto}://{ip}:{port}")
    except Exception as e:
        print(f"⚠️ Ошибка сбора Geonode: {e}")

    # 2. Proxyscrape API (RU, KZ, BY)
    try:
        url = 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=3000&country=RU,KZ,BY&ssl=all&anonymity=all'
        res = requests.get(url, timeout=5, headers=headers)
        if res.status_code == 200:
            for line in res.text.splitlines():
                line = line.strip()
                if line and ':' in line:
                    proxies.append(f"http://{line}")
    except Exception as e:
        print(f"⚠️ Ошибка сбора ProxyScrape: {e}")

    # 3. GitHub Lists
    try:
        url = 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'
        res = requests.get(url, timeout=5, headers=headers)
        if res.status_code == 200:
            for line in res.text.splitlines()[:50]:
                line = line.strip()
                if line and ':' in line:
                    proxies.append(f"http://{line}")
    except Exception:
        pass

    return list(set(proxies))

def test_single_proxy(proxy_url):
    """Быстрая проверка доступности целевого сайта через прокси"""
    try:
        proxies = {'http': proxy_url, 'https': proxy_url}
        r = requests.get("https://remanga.org", proxies=proxies, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code in [200, 301, 302]:
            return proxy_url
    except:
        pass
    return None

def find_working_proxy():
    """Параллельный поиск живого прокси за несколько секунд"""
    print("🌐 Ищу свежие бесплатные СНГ-прокси...")
    all_proxies = fetch_free_cis_proxies()
    print(f"📥 Найдено {len(all_proxies)} потенциальных прокси. Запускаю параллельный тест...")
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(test_single_proxy, p): p for p in all_proxies}
        for future in as_completed(futures):
            res = future.result()
            if res:
                print(f"🎯 Найден быстрый рабочий прокси: {res}")
                return res
    return None

def setup_browser_with_proxy(p, is_github):
    """Умный запуск браузера с подбором прокси"""
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # 1. ЕСЛИ ЗАПУСК ЛОКАЛЬНЫЙ (НА ПК) - ПРОКСИ НЕ НУЖНЫ
    if not is_github:
        print("💻 Локальный запуск: прямой трафик, браузер видимый.")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
        return browser, context, context.new_page()

    # 2. ЕСЛИ ЗАДАН КАСТОМНЫЙ ПРОКСИ В СЕКРЕТАХ (например, Webshare)
    custom_proxy = os.getenv('CUSTOM_PROXY') or os.getenv('PROXY_URL')
    if custom_proxy:
        print(f"🔑 Использую прокси из переменной окружения: {custom_proxy}")
        browser = p.chromium.launch(headless=True, proxy={"server": custom_proxy})
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
        return browser, context, context.new_page()

    # 3. ЕСЛИ ЕСТЬ ЛОКАЛЬНЫЙ proxies.json
    proxies_path = get_file_path('proxies.json')
    if os.path.exists(proxies_path):
        try:
            with open(proxies_path, 'r') as f:
                proxies_list = json.load(f)
            if proxies_list:
                print(f"📁 Загружен proxies.json ({len(proxies_list)} шт). Проверяю...")
                for p_data in proxies_list:
                    server = f"http://{p_data['ip_address']}:{p_data['port']}"
                    try:
                        b = p.chromium.launch(headless=True, proxy={"server": server})
                        ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
                        pg = ctx.new_page()
                        resp = pg.goto(TARGET_URL, timeout=12000, wait_until="domcontentloaded")
                        if resp and resp.status in [200, 301, 302]:
                            print(f"✅ Рабочий прокси из файла: {server}")
                            return b, ctx, pg
                        b.close()
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ Ошибка чтения proxies.json: {e}")

    # 4. АВТОМАТИЧЕСКИЙ БЕСПЛАТНЫЙ ПОИСК В СЕТИ
    print("☁️ Запуск на сервере/GitHub: включаю автоматический подбор бесплатного СНГ прокси...")
    working_proxy = find_working_proxy()
    
    if working_proxy:
        try:
            browser = p.chromium.launch(headless=True, proxy={"server": working_proxy})
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
            page = context.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            return browser, context, page
        except Exception as e:
            print(f"❌ Ошибка подключения через найденный прокси: {e}")

    # 5. ЕСЛИ ПРОКСИ НЕ НАЙДЕН - ПРОБУЕМ НАПРЯМУЮ
    print("⚠️ Прокси не найден. Пробую запуск напрямую (возможен 403 от Cloudflare/DDoS-Guard)...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent=user_agent)
    page = context.new_page()
    return browser, context, page

def run_dungeon_bot():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{timestamp}] Запуск задачи фарма катакомб...")
    
    is_github = 'GITHUB_ACTIONS' in os.environ or os.getenv('RUN_HEADLESS', 'false').lower() == 'true'
    
    with sync_playwright() as p:
        browser, context, page = setup_browser_with_proxy(p, is_github)
        
        if not browser:
            send_telegram_message("❌ Бот остановлен: не удалось инициализировать браузер.")
            return

        try:
            # Загружаем куки (если есть) в рабочий контекст
            cookies_path = get_file_path('cookies.txt')
            netscape_cookies = parse_netscape_cookies(cookies_path)
            if netscape_cookies:
                context.add_cookies(netscape_cookies)
                print("🍪 Куки успешно загружены.")
            
            # Переходим на страницу
            print(f"🔗 Переход на {TARGET_URL}...")
            resp = page.goto(TARGET_URL, timeout=40000, wait_until="domcontentloaded")
            
            if resp and resp.status in [403, 502, 503]:
                print(f"❌ Доступ заблокирован сайтом (HTTP {resp.status}). Нужен СНГ IP!")
                send_telegram_message(f"❌ Ошибка доступа: HTTP {resp.status}. Сервер заблокирован.")
                browser.close()
                return

        except Exception as e:
            print(f"Ошибка загрузки страницы: {e}")

        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        try:
            human_sleep(3, 5)
            
            # ==========================================
            # АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ (ПРИ НЕОБХОДИМОСТИ)
            # ==========================================
            try:
                login_btn = page.locator('text="Войти"').first
                if login_btn.is_visible(timeout=5000):
                    print("⚠️ Куки не сработали. Начинаю автоматический вход...")
                    login_btn.click()
                    human_sleep(2, 3)
                    
                    email_val = os.getenv('REMANGA_EMAIL', 'zavlatkamalov@gmail.com')
                    pass_val = os.getenv('REMANGA_PASSWORD', 'Zafarjon1224')
                    
                    email_field = page.locator('input[type="text"], input[type="email"], input[name="username"]').first
                    email_field.fill(email_val)
                    human_sleep(1, 2)
                    
                    pass_field = page.locator('input[type="password"]').first
                    pass_field.fill(pass_val)
                    human_sleep(1, 2)
                    
                    submit_btn = page.locator('button[type="submit"], button:has-text("Войти")').last
                    submit_btn.click()
                    
                    print("✅ Данные отправлены. Жду прогрузки аккаунта...")
                    human_sleep(6, 8)
                    page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
                    human_sleep(5, 7)
            except Exception:
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
