import time
import random
import schedule
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения для локального запуска
load_dotenv()

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return
    
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
    if 'GITHUB_WORKSPACE' in os.environ:
        cookies_path = Path(os.environ['GITHUB_WORKSPACE']) / 'test' / 'cookies.txt'
    else:
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
    print(f"\n[{timestamp}] Запуск задачи фарма катакомб...")
    send_telegram_message(f"🤖 Бот начал работу! ⏰ {timestamp}")
    
    with sync_playwright() as p:
        # Для локального теста поставить headless=False, чтобы видеть браузер
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Загружаем куки
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
            error_msg = f"❌ Не удалось открыть страницу: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
            browser.close()
            return
        
        # Закрываем всплывающее окно / рекламу
        try:
            close_btn = page.locator('button[aria-label="Закрыть"]')
            if close_btn.is_visible(timeout=5000):
                close_btn.click()
                print("✅ Всплывающее окно успешно закрыто!")
                human_sleep(2, 3)
        except Exception as e:
            print(f"Всплывающее окно не найдено или уже закрыто: {e}")

        run_count = 1
        
        while True:
            try:
                print(f"\n--- Запуск цикла прохода №{run_count} ---")
                
                # 1. Ищем элемент, содержащий строго иероглиф 寺
                kanji_element = page.locator('span.font-kanji', has_text='寺')
                kanji_element.first.wait_for(state="visible", timeout=20000)
                
                if kanji_element.count() > 0:
                    kanji_element.first.click()
                    print("✅ Успешно кликнул по иероглифу 寺!")
                else:
                    print("Иероглиф 寺 на карте не найден.")
                    break 
                
                human_sleep(2, 3)

                # 2. Нажимаем кнопку прохода («ПРОЙТИ СНОВА» или аналогичные)
                pass_button = page.locator('text=ПРОЙТИ СНОВА')
                try:
                    pass_button.wait_for(state="visible", timeout=5000)
                    is_disabled = pass_button.evaluate("node => node.disabled || node.getAttribute('aria-disabled') === 'true'")
                    if is_disabled:
                        print("Энергия закончилась! Кнопка прохода заблокирована.")
                        break
                    pass_button.click()
                except Exception as ex:
                    print(f"Кнопка 'ПРОЙТИ СНОВА' недоступна: {ex}")
                    break
                
                human_sleep(2, 3)

                # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)
  # 3. Нажимаем на кнопку с иероглифом 戰 (начало боя)
                try:
                    battle_btn = page.locator('text=戰')
                    battle_btn.wait_for(state="visible", timeout=5000)
                    battle_btn.click()
                    print("⚔️ Нажата кнопка боя (戰)!")
                except Exception as ex:
                    print(f"Кнопка боя (戰) не найдена: {ex}")
                
                # 4. Ждем завершения боя
                print("Жду завершения боя...")
                human_sleep(12, 16)

                # 5. Кликаем «К результатам»
                try:
                    page.locator('text=К результатам').click(timeout=8000)
                    print("✅ Нажато 'К результатам'")
                except Exception as e:
                    print(f"Не удалось нажать 'К результатам': {e}")
                    break
                
                human_sleep(2, 3)

                # 6. Закрываем оверлей результатов, чтобы вернуться на карту для следующего круга
                try:
                    page.locator('button[data-sentry-source-file="pve-result-overlay.tsx"]').click(timeout=8000)
                    print("✅ Оверлей результатов закрыт, возвращаемся на карту.")
                except Exception as e:
                    print(f"Не удалось закрыть оверлей результатов: {e}")
                    break
                
                run_count += 1
                print(f"🔄 Цикл №{run_count - 1} успешно завершен. Пауза перед следующим...")
                human_sleep(4, 6)
                
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                try:
                    page.screenshot(path="error_screenshot.png")
                    print("Скриншот экрана сохранен.")
                except:
                    pass
                break

        print("Фарм завершен. Закрываю браузер.")
        browser.close()
        send_telegram_message(f"✅ Фарм завершен! Всего циклов: {run_count - 1}")

if __name__ == "__main__":
    if 'GITHUB_ACTIONS' in os.environ:
        print("[GitHub Actions] Запуск бота...")
        run_dungeon_bot()
    else:
        print("[Локальный запуск] Запуск бота...")
        run_dungeon_bot()
