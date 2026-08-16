# 📋 Полная инструкция: Автоматизация бота через GitHub Actions

## 📌 Что мы сделали?

1. ✅ Создан файл `.github/workflows/bot.yml` — конфигурация GitHub Actions
2. ✅ Обновлен `bot.py` — работает как локально, так и в облаке
3. ✅ Создан `requirements.txt` — список зависимостей

---

## 🚀 Пошаговая инструкция

### **ШАГ 1: Инициализируем Git локально (если еще не сделано)**

```bash
cd /path/to/perviy
git init
git config user.name "Ваше Имя"
git config user.email "ваш_email@gmail.com"
```

### **ШАГ 2: Создаем .gitignore (чтобы не залить лишние файлы)**

Создай файл `.gitignore` в корне папки `perviy`:

```
__pycache__/
*.pyc
.pytest_cache/
.env
*.log
db.sqlite3
```

### **ШАГ 3: Коммитим файлы локально**

```bash
git add .
git commit -m "Initial commit: bot setup with GitHub Actions"
```

### **ШАГ 4: Создаем репозиторий на GitHub**

1. Заходим на **https://github.com/new**
2. Вводим имя репозитория: `remanga-bot` (или любое другое)
3. **Не инициализируем** README, .gitignore, license
4. Нажимаем **"Create repository"**

### **ШАГ 5: Подключаем локальный репозиторий к GitHub**

После создания репозитория GitHub покажет команды. Выполняем их:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/remanga-bot.git
git push -u origin main
```

**Где заменяем:**
- `YOUR_USERNAME` — твой логин на GitHub

### **ШАГ 6: Добавляем SECRET с cookies**

1. Заходим в **Settings** репозитория (верхний правый угол → Settings)
2. Слева нажимаем **Secrets and variables** → **Actions**
3. Нажимаем кнопку **"New repository secret"**
4. **Name:** `COOKIES_TXT`
5. **Value:** Открываем файл `cookies.txt` с локального компьютера, копируем всё содержимое и вставляем сюда
6. Нажимаем **"Add secret"**

> ⚠️ **ВАЖНО:** GitHub никогда не покажет значение секрета! Это безопасно.

### **ШАГ 7: Проверяем, что всё загрузилось**

1. Заходим в вкладку **Code** репозитория
2. Должны видеть файлы:
   - `.github/workflows/bot.yml`
   - `test/bot.py`
   - `test/cookies.txt`
   - `requirements.txt`
   - И другие файлы проекта

### **ШАГ 8: Запускаем бота первый раз (вручную)**

1. Переходим на вкладку **Actions** в репозитории
2. Слева выбираем **"Запуск бота по расписанию"** (название workflow)
3. Нажимаем кнопку **"Run workflow"** → **"Run workflow"**
4. Смотрим логи в реальном времени!

---

## ⏰ Расписание запуска

**По умолчанию бот запускается каждый день в 10:00 UTC.**

Чтобы изменить время, отредактируй строку в `.github/workflows/bot.yml`:

```yaml
schedule:
  - cron: '0 10 * * *'
```

**Примеры расписания (формат cron):**
- `'0 10 * * *'` — каждый день в 10:00 UTC ✅ (текущее)
- `'0 8 * * *'` — каждый день в 8:00 UTC
- `'0 14 * * *'` — каждый день в 14:00 UTC
- `'0 10,14 * * *'` — в 10:00 и 14:00 UTC
- `'0 10 * * 1-5'` — только в будни в 10:00 UTC

Найти нужное время: https://crontab.guru/

---

## 🔐 Как обновить cookies?

Если куки истекут (обычно на это требуется месяц), выполни:

1. Экспортируй новые куки из браузера (как раньше)
2. Заходим в **Settings** → **Secrets and variables** → **Actions**
3. Нажимаем на `COOKIES_TXT` → **Update secret**
4. Вставляем новое содержимое файла `cookies.txt`
5. Нажимаем **"Update secret"**

---

## 📊 Как смотреть логи выполнения?

1. Вкладка **Actions** в репозитории
2. Выбираем последний запуск
3. Нажимаем на **"run_bot"** job
4. Видим логи каждого шага (установка зависимостей, запуск бота и т.д.)

---

## 🆘 Если что-то пошло не так?

**Проблема:** Ошибка `No such file or directory: cookies.txt`
- **Решение:** Проверь, что SECRET `COOKIES_TXT` добавлен и содержит правильные куки

**Проблема:** Workflow не запускается
- **Решение:** Проверь, что файл `.github/workflows/bot.yml` правильно загрузился на GitHub

**Проблема:** Playwright не установлен
- **Решение:** В workflow установлены `playwright install`, должно помочь

---

## 📝 Итого, что делать одной командой (если Git уже настроен)

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push origin main
```

Затем добавить SECRET через веб-интерфейс GitHub.

**Готово! 🎉 Теперь бот будет запускаться автоматически!**
