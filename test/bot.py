import time
import random
import os
import json
import subprocess
import sys
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth 
import requests

# --- ЛОГИКА СОСТОЯНИЯ (STATE MACHINE) ---

def get_current_date():
    return time.strftime('%Y-%m-%d')

def load_state():
    """Загружает состояние фарма из файла state.json"""
    default_state = {
        "date": get_current_date(),
        "status": "pending",
        "runs_done": 0,
        "target_runs": -1  # -1 значит, что мы еще не считали энергию сегодня
    }
    state_file = Path(__file__).parent / 'state.json'
    
    try:
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            # Если начался новый день - сбрасываем прогресс
            if state.get("date") != get_current_date():
                return default_state
            return state
    except Exception as e:
        print(f"⚠️ Ошибка чтения state.json, начинаем с нуля: {e}")
        
    return default_state

def save_and_push_state(state):
    """Сохраняет состояние локально и пушит в GitHub"""
    state_file = Path(__file__).parent / 'state.json'
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)
        
    print(f"💾 Прогресс сохранен: {state['runs_done']} / {state['target_runs']} (Статус: {state['status']})")
    
    if 'GITHUB_ACTIONS' in os.environ:
        try:
            subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], check=False)
            subprocess.run(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'], check=False)
            subprocess.run(['git', 'add', str(state_file)], check=True)
            res = subprocess.run(['git', 'commit', '-m', f"🤖 Прогресс: {state['runs_done']}/{state['target_runs']} ({state['status']})"], capture_output=True)
            
            if res.returncode == 0:
                subprocess.run(['git', 'pull', '--rebase'], check=False) # Подтягиваем изменения, если другой комп что-то запушил
                subprocess.run(['git', 'push'], check=True)
                print("☁️ Состояние успешно отправлено в GitHub!")
        except Exception as e:
            print(f"⚠️ Ошибка при отправке в GitHub: {e}")

# --- БАЗОВЫЕ ФУНКЦИИ ---

def send_telegram_message(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": message}, timeout=10)
        except: pass

def human_sleep(min_sec=2, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def get_cookies_path():
    if 'GITHUB_WORKSPACE' in os.environ:
        return str(Path(os.environ['GITHUB_WORKSPACE']) / 'test' / 'cookies.txt')
    return str(Path(__file__).parent / 'cookies.txt')

def parse_netscape_cookies(file_path):
    cookies = []
    if not os.path.exists(file_path): return cookies
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies.append({
                    "name": parts[5], "value": parts[6], "domain": parts[0], "path": parts[2],
                    "secure": parts[3].upper() == "TRUE", "httpOnly": False,
                    "expires": int(parts[4]) if parts[4].isdigit() else None
                })
    return cookies

# --- ОСНОВНАЯ ЛОГИКА ---

def run_dungeon_bot():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Проверка состояния фарма...")
    
    state = load_state()
    
    if state["status"] == "done" or (state["target_runs"] != -1 and state["runs_done"] >= state["target_runs"]):
        print(f"✅ На сегодня фарм уже завершен ({state['runs_done']}/{state['target_runs']})! Бот спит до завтра.")
        if state["status"] != "done":
            state["status"] = "done"
            save_and_push_state(state)
        sys.exit(0)
        
    print(f"🔄 Запуск! Сделано проходов: {state['runs_done']}. Цель: {state['target_runs'] if state['target_runs'] != -1 else 'Еще не рассчитана'}")
    state["status"] = "in_progress"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = context.new_page()
        
        try:
            cookies = parse_netscape_cookies(get_cookies_path())
            if cookies: context.add_cookies(cookies)
        except Exception as e: print(f"Ошибка куки: {e}")

        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        try:
            page.goto("https://реманга.орг/murim-cards#/map", timeout=60000, wait_until="domcontentloaded")
            human_sleep(4, 6)
            
            # АВТО-ВХОД
            if page.locator('text="Войти"').first.is_visible(timeout=5000):
                print("⚠️ Начинаю автоматический вход...")
                page.locator('text="Войти"').first.click()
                human_sleep(2, 3)
                page.locator('input[type="text"], input[type="email"], input[name="username"]').first.fill("zavlatkamalov@gmail.com")
                human_sleep(1, 2)
                page.locator('input[type="password"]').first.fill("Zafarjon1224")
                human_sleep(1, 2)
                page.locator('button[type="submit"], button:has-text("Войти")').last.click()
                human_sleep(6, 8)
                page.goto("https://реманга.орг/murim-cards#/map", timeout=60000, wait_until="domcontentloaded")
                human_sleep(4, 6)
        except Exception as e:
            print(f"❌ Ошибка входа: {e}")
            return

        try:
            if page.locator('button[aria-label="Закрыть"]').is_visible(timeout=3000):
                page.locator('button[aria-label="Закрыть"]').click()
        except: pass

        # ВЫЧИСЛЕНИЕ ЭНЕРГИИ И МАКС. ПРОХОДОВ (Если еще не считали сегодня)
        if state["target_runs"] == -1:
            try:
                # Ищем на странице текст в формате "60 / 100" (любые цифры со слешем)
                print("🔍 Ищу количество энергии на экране...")
                energy_text = page.locator(':text-matches("^[0-9]+\\s*/\\s*[0-9]+$")').first.inner_text(timeout=5000)
                current_energy = int(re.search(r'^(\d+)', energy_text.strip()).group(1))
                
                # Математика: текущая энергия / 8
                state["target_runs"] = current_energy // 8
                print(f"🔋 Найдена энергия: {energy_text}. Запланировано проходов на сегодня: {state['target_runs']}")
                
                if state["target_runs"] == 0:
                    print("Энергии не хватает даже на 1 проход. Завершаю работу на сегодня.")
                    state["status"] = "done"
                    save_and_push_state(state)
                    browser.close()
                    return
                    
                save_and_push_state(state)
            except Exception as e:
                print("⚠️ Не удалось найти цифры энергии. Ставлю цель по умолчанию: 12 проходов.")
                state["target_runs"] = 12

        # ЦИКЛ ФАРМА (Крутим, пока не выполним норму target_runs)
        while state["runs_done"] < state["target_runs"]:
            try:
                print(f"\n--- Запуск цикла прохода №{state['runs_done'] + 1} из {state['target_runs']} ---")
                
                kanji = page.locator('span.font-kanji', has_text='寺')
                kanji.first.wait_for(state="visible", timeout=15000)
                if kanji.count() > 0:
                    kanji.first.click()
                else:
                    print("Иероглиф 寺 не найден.")
                    break 
                
                human_sleep(2, 3)

                pass_button = page.locator('text=ПРОЙТИ СНОВА')
                try:
                    pass_button.wait_for(state="visible", timeout=5000)
                    if pass_button.evaluate("node => node.disabled || node.getAttribute('aria-disabled') === 'true'"):
                        print("🔴 ЭНЕРГИЯ ЗАКОНЧИЛАСЬ РАНЬШЕ ВРЕМЕНИ! (Возможно, сервер обновил данные).")
                        state["status"] = "done"
                        save_and_push_state(state)
                        break
                    pass_button.click()
                except Exception as ex:
                    print(f"Кнопка 'ПРОЙТИ СНОВА' недоступна: {ex}")
                    break
                
                human_sleep(2, 3)

                try: page.locator('text=戰').click(timeout=5000)
                except: pass
                
                print("Жду завершения боя (12-16 сек)...")
                human_sleep(12, 16)

                try: page.locator('text=К результатам').click(timeout=8000)
                except: break
                human_sleep(2, 3)

                try: page.locator('button[data-sentry-source-file="pve-result-overlay.tsx"]').click(timeout=8000)
                except: break
                
                # УВЕЛИЧИВАЕМ СЧЕТЧИК И СОХРАНЯЕМ ПРОГРЕСС!
                state["runs_done"] += 1
                print(f"✅ Цикл завершен. Прогресс: {state['runs_done']} / {state['target_runs']}")
                
                # Сохраняем после каждого успешного прохода, чтобы при падении ПК ничего не потерять
                save_and_push_state(state)
                
                human_sleep(4, 6)
                
            except Exception as e:
                print(f"❌ Непредвиденная ошибка: {e}")
                break

        if state["runs_done"] >= state["target_runs"]:
            print("🎉 ВСЯ ЭНЕРГИЯ ИСТРАЧЕНА (ПЛАН ВЫПОЛНЕН)!")
            state["status"] = "done"
            save_and_push_state(state)
            send_telegram_message(f"✅ Фарм окончен! Сделано {state['runs_done']} из {state['target_runs']} запланированных проходов.")

        print("Закрываю браузер.")
        browser.close()

if __name__ == "__main__":
    run_dungeon_bot()
