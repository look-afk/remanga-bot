try:
            page.goto("https://remanga.org/murim-cards#/map", timeout=60000)
            human_sleep(4, 6) # Даем время странице и рекламе прогрузиться
        except Exception as e:
            error_msg = f"❌ Не удалось открыть страницу: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
            browser.close()
            return
        
        # Универсальное закрытие рекламы, баннеров и промо-окон
        print("Проверяю наличие рекламы или всплывающих окон...")
        close_selectors = [
            'button[aria-label="Закрыть промо подписки"]',
            'button[aria-label="Закрыть"]',
            '.modal-close',
            '.close-btn',
            'button:has-text("✕")',
            'button:has-text("X")',
            '[class*="close"]'
        ]
        
        for selector in close_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"Закрыто всплывающее окно/реклама.")
                    human_sleep(1, 2)
            except:
                pass
