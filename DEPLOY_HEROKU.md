# Деплой на Heroku

## Передумови

```bash
# Встановіть Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Увійдіть у Heroku
heroku login
```

## Кроки деплою

### 1. Створіть новий Heroku app

```bash
# Замініть job-parser на улюблену назву
heroku create job-parser
```

### 2. Встановіть обов'язкові змінні оточення

```bash
# TELEGRAM_BOT_TOKEN - отримайте від BotFather в Telegram
heroku config:set TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN" -a job-parser

# TELEGRAM_CHAT_ID - ID чату для отправки повідомлень
heroku config:set TELEGRAM_CHAT_ID="YOUR_CHAT_ID" -a job-parser
```

### 3. Виберіть размір dyno залежно від потреб

```bash
# Для тестування (free dyno - спить після бездіяльності)
heroku ps:type free -a job-parser

# Для постійної роботи (платний)
heroku ps:type eco -a job-parser
heroku ps:scale worker=1 -a job-parser
```

### 4. Деплойте додаток

```bash
git push heroku main
# або
git push heroku master
```

### 5. Спостерігайте за логами

```bash
heroku logs --tail -a job-parser
```

## Процеси

### Release phase
При кожному деплою (один раз) запускається:
```
dry-run --pages 5
```
Це завантажує перші 5 сторінок із кожного джерела без запису в БД.

### Worker dyno
Постійно працює (якщо включено):
```
worker - сканує джерела кожні 2 години
```

Після першого dry-run, worker почне шукати нові вакансії згідно `JOB_PARSER_INTERVAL_MINUTES` (за замовч. 120 хв).

## Необов'язкові змінні оточення

```bash
# Інтервал сканування в хвилинах (за замовч. 120)
heroku config:set JOB_PARSER_INTERVAL_MINUTES="120" -a job-parser
```

## Важливо про персистентність даних

Heroku має **ephemeral filesystem** - файли не зберігаються між рестартами dyno (~24 години).

Для роботи бота потрібна БД, щоб не надсилати дубльовані вакансії. Варіанти:

1. **SQLite на ephemeral FS** (тек. конфіг)
   - Даних втрачаються кожні ~24 години
   - Відправляються дубльовані вакансії
   - Безкоштовно

2. **Heroku Postgres** (рекомендовано)
   - Персистентна БД
   - Коштує ~$15/měsíц (або більше за більший dyno)
   - Встановлення:
   ```bash
   heroku addons:create heroku-postgresql:mini -a job-parser
   ```

3. **AWS RDS / інші DB сервіси**
   - Налаштування середовища для підключення:
   ```bash
   heroku config:set DATABASE_URL="postgresql://..." -a job-parser
   ```

## Моніторинг

```bash
# Див. статус процесів
heroku ps -a job-parser

# Див. останні логи
heroku logs -a job-parser

# Див. переважні логи (останні 2 години)
heroku logs --since 2h -a job-parser

# Див. логи тільки worker
heroku logs --dyno worker -a job-parser
```

## Тестування перед деплоєм

```bash
# Запустіть тести локально
python -m pytest tests/ -v

# Запустіть dry-run локально
python -m job_parser.cli dry-run --pages 1

# Або через venv
.venv/bin/python -m job_parser.cli dry-run --pages 5
```

## Скасування деплою / Видалення

```bash
# Видаліть додаток
heroku apps:destroy -a job-parser

# Або просто зупиніть worker без видалення
heroku ps:scale worker=0 -a job-parser
```

## Debugging

```bash
# Запустіть bash shell на Heroku
heroku run bash -a job-parser

# Або запустіть команду
heroku run python -m job_parser.cli dry-run --pages 1 -a job-parser
```
