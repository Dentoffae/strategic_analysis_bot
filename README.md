# Strategic Analysis Bot Generator

LangChain-пайплайн из **6 цепочек**, который принимает описание компании и автоматически генерирует готовый Telegram-бот стратегического анализа.

---

## Как это работает

```
python script.py "ОАЭ, Aquiline International Corporation, www.aquiline-aero.com"
```

```
[1/6] analysis_chain   → разбор задания: цели, сущности, ограничения
[2/6] tools_chain      → подбор библиотек, паттернов, архитектурных решений
[3/6] structure_chain  → скелет кода: модули, классы, сигнатуры функций
[4/6] code_chain       → реализация полного Python-кода бота
[5/6] review_chain     → проверка и исправление кода
[6/6] save_chain       → валидация синтаксиса + сохранение telegram_bot.py
```

На выходе — `telegram_bot.py`, который сразу готов к запуску.

---

## Что умеет сгенерированный бот

| Команда    | Действие                                              |
|------------|-------------------------------------------------------|
| `/start`   | Приветствие и инструкция                              |
| `/analyze` | Запросить данные о компании и запустить полный анализ |
| `/help`    | Справка                                               |
| `/pdf`     | Выгрузить последний отчёт в PDF                       |

После ввода названия компании, страны и ссылки бот последовательно проводит:

- **SWOT-анализ** — сильные/слабые стороны, возможности, угрозы
- **PESTEL-анализ** — политика, экономика, социум, технологии, экология, право
- **Пять сил Портера** — конкуренция, поставщики, покупатели, субституты, новые игроки
- **Матрица Ансоффа** — четыре стратегии роста

Каждый блок анализа — отдельная LangChain-цепочка (LCEL). После анализа пользователь получает кнопку для скачивания PDF-отчёта.

---

## Структура проекта

```
ANALYSIS/
├── script.py          # 4-chain генератор (запускать этот файл)
├── telegram_bot.py    # генерируется автоматически
├── requirements.txt
├── .env               # токены (не коммитить!)
└── .env.example       # шаблон переменных окружения
```

---

## Быстрый старт

### 1. Клонировать / создать окружение

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить `.env`

Скопируйте шаблон и заполните значения:

```bash
cp .env.example .env
```

```dotenv
OPENAI_API_KEY=sk-...          # ключ OpenAI
OPENAI_MODEL=gpt-4o-mini       # модель (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
OPENAI_TEMPERATURE=0.2         # температура генерации
OPENAI_BASE_URL=               # оставить пустым для официального OpenAI
BOT_TOKEN=123456:ABC...        # токен от @BotFather
```

### 4. Запустить генератор

```bash
python script.py "ОАЭ, Aquiline International Corporation, www.aquiline-aero.com"
```

Пример вывода:

```
════════════════════════════════════════════════════════════════
  STRATEGIC ANALYSIS BOT GENERATOR  |  LangChain Pipeline
════════════════════════════════════════════════════════════════

  Вход  : ОАЭ, Aquiline International Corporation, www.aquiline-aero.com
  Модель: gpt-4o-mini

[1/4] analysis_chain   — формирую техническую спецификацию …
      ✓ Спецификация готова

[2/4] code_chain       — генерирую Python-код Telegram-бота …
      ✓ Код сгенерирован

[3/4] review_chain     — проверяю и исправляю код …
      ✓ Код проверен

[4/4] save_chain       — сохраняю в telegram_bot.py …

════════════════════════════════════════════════════════════════
  ГОТОВО
════════════════════════════════════════════════════════════════
  Файл         : telegram_bot.py
  Строк        : 420
  Размер       : 18.3 КБ
  Синтаксис    : ✓
```

### 5. Запустить сгенерированный бот

```bash
python telegram_bot.py
```

---

## Архитектура пайплайна

```
company_input
      │
      ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 1 — analysis_chain                        │
│  Разбор задания: цели, сущности, ограничения     │
│  ChatPromptTemplate | llm | StrOutputParser      │
│  → task_analysis (JSON)                          │
└──────────────────────┬───────────────────────────┘
                       │ task_analysis
                       ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 2 — tools_chain                           │
│  Подбор библиотек, паттернов, решений            │
│  ChatPromptTemplate | llm | StrOutputParser      │
│  → tools_selection (JSON)                        │
└──────────────────────┬───────────────────────────┘
                       │ task_analysis + tools_selection
                       ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 3 — structure_chain                       │
│  Скелет кода: модули, классы, сигнатуры          │
│  ChatPromptTemplate | llm | StrOutputParser      │
│  → code_structure (blueprint)                    │
└──────────────────────┬───────────────────────────┘
                       │ code_structure + task_analysis + tools_selection
                       ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 4 — code_chain                            │
│  Реализация каждой функции из скелета            │
│  ChatPromptTemplate | llm | StrOutputParser      │
│  → raw_code (Python)                             │
└──────────────────────┬───────────────────────────┘
                       │ raw_code
                       ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 5 — review_chain                          │
│  Проверка: синтаксис, импорты, aiogram API       │
│  ChatPromptTemplate | llm | StrOutputParser      │
│  → reviewed_code (Python)                        │
└──────────────────────┬───────────────────────────┘
                       │ reviewed_code
                       ▼
┌──────────────────────────────────────────────────┐
│  CHAIN 6 — save_chain                            │
│  Очистка markdown, ast.parse(), запись файла     │
│  RunnableLambda(_clean_and_save)                 │
│  → telegram_bot.py                               │
└──────────────────────────────────────────────────┘
```

### Внутри `telegram_bot.py` (после генерации)

```
user_message (компания)
      │
      ├──▶ swot_chain   (ChatPromptTemplate | ChatOpenAI | StrOutputParser)
      ├──▶ pestel_chain
      ├──▶ porter_chain
      └──▶ ansoff_chain
                 │
                 ▼
      Полный отчёт → Telegram (HTML)
                 │
                 └──▶ PDF (ReportLab) → FSInputFile → Telegram
```

---

## Зависимости

| Пакет | Версия | Назначение |
|-------|--------|------------|
| `langchain` | ≥ 1.2 | Оркестрация цепочек |
| `langchain-openai` | ≥ 1.1 | ChatOpenAI интеграция |
| `langchain-core` | ≥ 1.2 | LCEL, промпты, парсеры |
| `openai` | ≥ 2.0 | OpenAI Python SDK |
| `aiogram` | ≥ 3.7 | Telegram Bot API |
| `reportlab` | ≥ 4.1 | Генерация PDF |
| `python-dotenv` | ≥ 1.0 | Переменные окружения |
| `aiohttp` | ≥ 3.9 | Async HTTP (aiogram) |

---

## Частые вопросы

**Какую модель лучше использовать?**
`gpt-4o-mini` — хороший баланс цены и качества. Для более детального анализа используйте `gpt-4o`.

**Можно ли использовать другой провайдер (не OpenAI)?**
Да — установите `OPENAI_BASE_URL` на адрес совместимого API (например, Together AI, Groq, local Ollama).

**Бот не запускается после генерации?**
Запустите `python -c "import ast; ast.parse(open('telegram_bot.py', encoding='utf-8').read())"` — если вывод пустой, синтаксис корректен. Проверьте `.env` на наличие `BOT_TOKEN` и `OPENAI_API_KEY`.

**Как изменить язык анализа?**
В `script.py` в системных промптах `_CODE_SYSTEM` найдите упоминание `Russian` и замените на нужный язык.
