#!/usr/bin/env python3
"""
LangChain 6-Chain Pipeline — Strategic Analysis Telegram Bot Generator
=======================================================================
Chains:
  1. analysis_chain   — анализирует задание: извлекает сущности, цели, ограничения
  2. tools_chain      — подбирает библиотеки, паттерны и архитектурные решения
  3. structure_chain  — строит скелет кода: модули, классы, сигнатуры функций
  4. code_chain       — реализует полный рабочий Python-код Telegram-бота
  5. review_chain     — проверяет и исправляет сгенерированный код
  6. save_chain       — очищает, валидирует синтаксис, сохраняет файл

Usage:
  python script.py "ОАЭ, Aquiline International Corporation, www.aquiline-aero.com"

Output:
  telegram_bot.py  — готовый к запуску Telegram-бот стратегического анализа
"""

import sys
import os
import ast
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# ---------------------------------------------------------------------------
# Загрузка переменных окружения
# ---------------------------------------------------------------------------
load_dotenv()

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

if not _OPENAI_API_KEY:
    sys.exit("❌  Переменная OPENAI_API_KEY не задана. Добавьте её в .env")

llm = ChatOpenAI(
    model=_MODEL,
    temperature=_TEMPERATURE,
    api_key=_OPENAI_API_KEY,
    base_url=_OPENAI_BASE_URL,
    max_tokens=4096,
)

# ===========================================================================
# CHAIN 1 — analysis_chain
# Анализирует задание: извлекает сущности, цели, ограничения и требования.
# Входные данные — произвольное описание компании от пользователя.
# Выходные данные — структурированный JSON-документ с полным разбором задачи.
# ===========================================================================

_ANALYSIS_SYSTEM = """\
Ты — senior business analyst и software architect.

Получи описание компании (страна, название, сайт/соцсеть) и проведи \
полный разбор задачи на создание Telegram-бота стратегического анализа.

Верни СТРОГО JSON-объект (без markdown-блоков) следующей структуры:
{{
  "task_summary": "<одно предложение — суть задачи>",
  "entities": {{
    "country": "<страна>",
    "company_name": "<название компании>",
    "website": "<сайт или соц. сеть>",
    "industry": "<предполагаемая отрасль>"
  }},
  "goals": [
    "<цель 1>",
    "<цель 2>"
  ],
  "constraints": [
    "<ограничение 1 — технологическое или бизнесовое>"
  ],
  "analysis_frameworks": {{
    "SWOT":    "<одна строка — что именно анализировать для данной компании>",
    "PESTEL":  "<одна строка>",
    "Porter":  "<одна строка>",
    "Ansoff":  "<одна строка>"
  }},
  "bot_requirements": {{
    "commands": ["/start", "/analyze", "/help", "/pdf"],
    "states": ["waiting_for_input", "analyzing"],
    "response_format": "HTML с эмодзи и разделами",
    "pdf_export": true,
    "language": "Russian",
    "error_handling": "дружелюбные сообщения на русском"
  }},
  "non_functional": {{
    "message_split": true,
    "max_message_chars": 4000,
    "async_required": true,
    "env_vars": ["BOT_TOKEN", "OPENAI_API_KEY"]
  }}
}}

Верни ТОЛЬКО валидный JSON без объяснений."""

analysis_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _ANALYSIS_SYSTEM),
        ("human", "Описание компании: {company_input}\n\nПроведи полный анализ задания."),
    ])
    | llm
    | StrOutputParser()
)

# ===========================================================================
# CHAIN 2 — tools_chain
# Подбирает конкретные инструменты, библиотеки и паттерны на основе анализа.
# Вход — JSON-разбор задачи из analysis_chain.
# Выход — обоснованный список технологических решений в формате JSON.
# ===========================================================================

_TOOLS_SYSTEM = """\
Ты — tech lead, специализирующийся на Python-экосистеме и LangChain.

На основе разбора задачи подбери оптимальный набор инструментов и \
архитектурных решений для реализации Telegram-бота стратегического анализа.

Верни СТРОГО JSON-объект (без markdown-блоков):
{{
  "telegram_framework": {{
    "library": "aiogram",
    "version": ">=3.7",
    "pattern": "Router + FSM",
    "rationale": "<почему aiogram 3.x и именно такой паттерн>"
  }},
  "llm_framework": {{
    "library": "langchain + langchain-openai",
    "pattern": "LCEL (| pipe operator)",
    "chains": [
      {{"name": "swot_chain",   "type": "ChatPromptTemplate | ChatOpenAI | StrOutputParser"}},
      {{"name": "pestel_chain", "type": "ChatPromptTemplate | ChatOpenAI | StrOutputParser"}},
      {{"name": "porter_chain", "type": "ChatPromptTemplate | ChatOpenAI | StrOutputParser"}},
      {{"name": "ansoff_chain", "type": "ChatPromptTemplate | ChatOpenAI | StrOutputParser"}}
    ],
    "rationale": "<почему LCEL и 4 отдельные цепочки>"
  }},
  "pdf_tool": {{
    "library": "reportlab",
    "encoding_strategy": "<как решить проблему кириллицы: транслитерация / latin-1 замена>",
    "rationale": "<почему reportlab>"
  }},
  "state_management": {{
    "tool": "aiogram FSM + MemoryStorage",
    "states": ["Form.waiting_input", "Form.processing"],
    "rationale": "<почему FSM>"
  }},
  "env_management": {{
    "tool": "python-dotenv",
    "vars": ["BOT_TOKEN", "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_TEMPERATURE"]
  }},
  "message_handling": {{
    "split_strategy": "split по \\n до 4000 символов",
    "parse_mode": "HTML",
    "rationale": "<почему HTML, а не Markdown>"
  }},
  "additional_packages": ["aiohttp", "python-dotenv"],
  "design_decisions": [
    "<решение 1 — например, хранить последний PDF в словаре user_reports>",
    "<решение 2 — например, запускать 4 LangChain-цепочки последовательно, не параллельно>"
  ]
}}

Верни ТОЛЬКО валидный JSON без объяснений."""

tools_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _TOOLS_SYSTEM),
        ("human", "Разбор задачи:\n{task_analysis}\n\nПодбери инструменты и архитектурные решения."),
    ])
    | llm
    | StrOutputParser()
)

# ===========================================================================
# CHAIN 3 — structure_chain
# Создаёт детальный скелет кода: модули, классы, сигнатуры функций, потоки данных.
# Вход — JSON из analysis_chain + JSON из tools_chain.
# Выход — текстовый blueprint с псевдокодом и сигнатурами.
# ===========================================================================

_STRUCTURE_SYSTEM = """\
Ты — senior Python developer. На основе разбора задачи и выбранных инструментов \
построй детальный скелет (blueprint) Python-скрипта Telegram-бота.

Скелет должен содержать:

1. СЕКЦИЯ ИМПОРТОВ
   Перечисли все необходимые import-строки.

2. КОНСТАНТЫ И ИНИЦИАЛИЗАЦИЯ
   - load_dotenv()
   - Bot, Dispatcher, Router, FSM Storage
   - ChatOpenAI instance
   - user_reports: dict[int, str] — хранение путей к PDF

3. FSM СОСТОЯНИЯ
   class AnalysisForm(StatesGroup):
       waiting_input: State
       processing: State

4. LANGCHAIN ЦЕПОЧКИ (сигнатуры и промпт-заглушки)
   swot_chain   = ChatPromptTemplate([...]) | llm | StrOutputParser()
   pestel_chain = ...
   porter_chain = ...
   ansoff_chain = ...

5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (только сигнатуры + docstring)
   def split_message(text: str, limit: int = 4000) -> list[str]: ...
   def transliterate(text: str) -> str: ...
   def generate_pdf(company: str, swot: str, pestel: str, porter: str, ansoff: str) -> str: ...

6. ОБРАБОТЧИКИ КОМАНД (только сигнатуры + что делает)
   async def cmd_start(message: Message) -> None: ...
   async def cmd_help(message: Message) -> None: ...
   async def cmd_analyze(message: Message, state: FSMContext) -> None: ...
   async def cmd_pdf(message: Message) -> None: ...
   async def process_company_input(message: Message, state: FSMContext) -> None: ...

7. ТОЧКА ВХОДА
   async def main() -> None: ...
   if __name__ == "__main__": asyncio.run(main())

Верни скелет как текстовый документ (не JSON, не Python-код), \
используя форматирование с заголовками и отступами. Без объяснений."""

structure_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _STRUCTURE_SYSTEM),
        ("human", (
            "Разбор задачи:\n{task_analysis}\n\n"
            "Выбранные инструменты:\n{tools_selection}\n\n"
            "Построй детальный скелет кода."
        )),
    ])
    | llm
    | StrOutputParser()
)

# ===========================================================================
# CHAIN 4 — code_chain
# Реализует полный рабочий Python-код на основе скелета из structure_chain.
# Вход — скелет кода + разбор задачи + выбранные инструменты.
# ===========================================================================

_CODE_SYSTEM = """\
Ты — опытный Python-разработчик. Реализуй ПОЛНЫЙ, РАБОЧИЙ скрипт Telegram-бота \
по готовому скелету кода и технической спецификации.

═══════════════════════════════════════════════════════════
ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
═══════════════════════════════════════════════════════════

1. AIOGRAM 3.x
   - from aiogram import Bot, Dispatcher, Router, F
   - from aiogram.filters import Command
   - from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
   - from aiogram.utils.keyboard import InlineKeyboardBuilder
   - Декораторы: @router.message(Command("cmd"))
   - dp.include_router(router)

2. LANGCHAIN (LCEL-стиль)
   - from langchain_openai import ChatOpenAI
   - from langchain_core.prompts import ChatPromptTemplate
   - from langchain_core.output_parsers import StrOutputParser
   - Четыре отдельные цепочки:
       • swot_chain   — SWOT-анализ
       • pestel_chain — PESTEL-анализ
       • porter_chain — Пять сил Портера
       • ansoff_chain — Матрица Ансоффа
   - Каждая цепочка: ChatPromptTemplate.from_messages([...]) | llm | StrOutputParser()

3. ПРОМПТЫ (детальные, только русский язык)
   Для каждого фреймворка — отдельный system prompt, содержащий:
   - Чёткую методологию (описание каждого компонента)
   - Требование давать детальный ответ объёмом не менее 400 слов
   - Требование структурировать ответ заголовками и подпунктами
   - Указание учитывать отрасль и страну компании
   Используй полный текст промптов, НЕ заглушки типа "...".

4. PDF-ОТЧЁТ (ReportLab)
   - Генерируется после полного анализа
   - Используй встроенный шрифт Helvetica (избегай ошибок с кириллицей)
   - Текст в PDF: транслитерировать кириллицу ИЛИ использовать font encoding latin-1
   - Отправляется по команде /pdf или кнопкой после анализа
   - Файл: report_<timestamp>.pdf

5. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
   - BOT_TOKEN и OPENAI_API_KEY из .env через python-dotenv
   - load_dotenv() вызывается в начале файла

6. РАЗБИВКА ДЛИННЫХ СООБЩЕНИЙ
   - Функция split_message(text, limit=4000) -> List[str]
   - Telegram-лимит: 4096 символов на сообщение

7. ОБРАБОТКА ОШИБОК
   - try/except вокруг AI-вызовов
   - Дружелюбные сообщения на русском при ошибке

8. ТОЧКА ВХОДА
   async def main():
       dp = Dispatcher()
       dp.include_router(router)
       await dp.start_polling(bot)

   if __name__ == "__main__":
       import asyncio
       asyncio.run(main())

9. КОМАНДЫ БОТА
   /start   — приветствие и инструкция
   /analyze — запросить данные о компании, затем провести полный анализ
   /help    — справка
   /pdf     — выслать последний PDF-отчёт

10. СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ
    - Использовать FSM (FiniteStateMachine) aiogram для хранения состояния диалога
    - from aiogram.fsm.state import State, StatesGroup
    - from aiogram.fsm.context import FSMContext
    - Состояния: ожидание ввода компании, обработка

═══════════════════════════════════════════════════════════
ВАЖНО:
- Никаких заглушек (pass, ..., TODO, placeholder)
- Каждая функция полностью реализована
- Вернуть ТОЛЬКО Python-код, начиная с #!/usr/bin/env python3
- Без markdown-блоков, без объяснений
═══════════════════════════════════════════════════════════"""

code_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _CODE_SYSTEM),
        ("human", (
            "Скелет кода:\n{code_structure}\n\n"
            "Разбор задачи:\n{task_analysis}\n\n"
            "Выбранные инструменты:\n{tools_selection}\n\n"
            "Реализуй каждую функцию полностью. Верни ТОЛЬКО Python-код."
        )),
    ])
    | llm
    | StrOutputParser()
)

# ===========================================================================
# CHAIN 5 — review_chain
# Проверяет и исправляет сгенерированный код
# ===========================================================================

_REVIEW_SYSTEM = """\
Ты — Python code reviewer и отладчик. Тщательно проверь предоставленный код \
Telegram-бота и исправь ВСЕ найденные проблемы.

ЧЕКЛИСТ ПРОВЕРКИ:
─────────────────────────────────────────────────────────
□ Синтаксис: нет SyntaxError (проверяй мысленно как ast.parse)
□ Все импорты присутствуют и корректны
□ aiogram 3.x API:
    - from aiogram import Bot, Dispatcher, Router, F
    - from aiogram.filters import Command
    - @router.message(Command("start")) — правильный синтаксис
    - dp.include_router(router) перед start_polling
    - FSMContext передаётся как аргумент обработчика
□ Каждая async-функция: await перед корутинами
□ BOT_TOKEN / OPENAI_API_KEY читаются из переменных окружения
□ main() — async, вызывается через asyncio.run(main())
□ LangChain LCEL: prompt | llm | parser
□ ReportLab: корректная генерация PDF (нет ошибок с кодировкой)
□ Разбивка сообщений на части ≤ 4000 символов
□ FSM-состояния объявлены и используются корректно
□ Нет неопределённых переменных или функций
□ Кириллица в PDF: либо транслитерация, либо latin-1 с заменой
─────────────────────────────────────────────────────────

Верни ТОЛЬКО исправленный Python-код без markdown-блоков и объяснений."""

review_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _REVIEW_SYSTEM),
        ("human", "Проверь и исправь код:\n\n{generated_code}"),
    ])
    | llm
    | StrOutputParser()
)

# ===========================================================================
# CHAIN 6 — save_chain
# Очищает markdown-артефакты, проверяет синтаксис Python, сохраняет файл
# ===========================================================================

def _clean_and_save(code: str) -> dict:
    """Очищает код от markdown, валидирует синтаксис, сохраняет в файл."""

    # Удаляем markdown code fences если LLM добавил их
    code = re.sub(r"^```(?:python)?\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"\n?```\s*$", "", code, flags=re.MULTILINE)
    code = code.strip()

    # Добавляем shebang если отсутствует
    if not code.startswith("#!"):
        code = "#!/usr/bin/env python3\n" + code

    # Проверка синтаксиса
    syntax_valid = True
    syntax_error = None
    try:
        ast.parse(code)
    except SyntaxError as exc:
        syntax_valid = False
        syntax_error = f"Строка {exc.lineno}: {exc.msg}"

    output_file = "telegram_bot.py"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)

    return {
        "output_file": output_file,
        "syntax_valid": syntax_valid,
        "syntax_error": syntax_error,
        "lines": code.count("\n") + 1,
        "size_kb": round(len(code.encode()) / 1024, 1),
    }


save_chain = RunnableLambda(_clean_and_save)

# ===========================================================================
# Pipeline runner — последовательно вызывает все 6 цепочек
# ===========================================================================

def run_pipeline(company_input: str) -> None:
    """Запускает полную 6-шаговую цепочку генерации бота для заданной компании."""

    _sep = "═" * 64
    print(f"\n{_sep}")
    print("  STRATEGIC ANALYSIS BOT GENERATOR  |  LangChain 6-Chain Pipeline")
    print(_sep)
    print(f"\n  Вход  : {company_input}")
    print(f"  Модель: {_MODEL}\n")

    # ── CHAIN 1 ── analysis_chain ─────────────────────────────────────────
    # Анализирует задание: цели, сущности, ограничения, требования к боту
    print("[1/6] analysis_chain   — анализирую задание …")
    task_analysis = analysis_chain.invoke({"company_input": company_input})
    print("      ✓ Задание разобрано\n")

    # ── CHAIN 2 ── tools_chain ────────────────────────────────────────────
    # Подбирает библиотеки, паттерны, архитектурные решения
    print("[2/6] tools_chain      — подбираю инструменты и паттерны …")
    tools_selection = tools_chain.invoke({"task_analysis": task_analysis})
    print("      ✓ Инструменты подобраны\n")

    # ── CHAIN 3 ── structure_chain ────────────────────────────────────────
    # Строит скелет кода: модули, классы, сигнатуры функций, потоки данных
    print("[3/6] structure_chain  — создаю структуру кода …")
    code_structure = structure_chain.invoke({
        "task_analysis": task_analysis,
        "tools_selection": tools_selection,
    })
    print("      ✓ Структура кода готова\n")

    # ── CHAIN 4 ── code_chain ──────────────────────────────────────────────
    # Реализует каждую функцию из скелета — полный рабочий Python-код
    print("[4/6] code_chain       — реализую код Telegram-бота …")
    raw_code = code_chain.invoke({
        "code_structure": code_structure,
        "task_analysis": task_analysis,
        "tools_selection": tools_selection,
    })
    print("      ✓ Код реализован\n")

    # ── CHAIN 5 ── review_chain ────────────────────────────────────────────
    # Проверяет и исправляет: синтаксис, импорты, aiogram API, async/await
    print("[5/6] review_chain     — проверяю и исправляю код …")
    reviewed_code = review_chain.invoke({"generated_code": raw_code})
    print("      ✓ Код проверен\n")

    # ── CHAIN 6 ── save_chain ──────────────────────────────────────────────
    # Очищает markdown-артефакты, валидирует ast.parse(), пишет файл
    print("[6/6] save_chain       — сохраняю в telegram_bot.py …")
    result = save_chain.invoke(reviewed_code)

    # ── Итог ──────────────────────────────────────────────────────────────
    ok_mark = "✓" if result["syntax_valid"] else "✗  ВНИМАНИЕ"
    print(f"\n{_sep}")
    print("  ГОТОВО")
    print(_sep)
    print(f"  Файл         : {result['output_file']}")
    print(f"  Строк        : {result['lines']}")
    print(f"  Размер       : {result['size_kb']} КБ")
    print(f"  Синтаксис    : {ok_mark}", end="")
    if result["syntax_error"]:
        print(f"  ({result['syntax_error']})", end="")
    print()

    print(f"""
  Следующие шаги:
  ─────────────────────────────────────────────────────────
  1. Убедитесь, что в .env заданы:
       BOT_TOKEN=<токен от @BotFather>
       OPENAI_API_KEY=<ключ OpenAI>

  2. Установите зависимости:
       pip install aiogram langchain langchain-openai reportlab python-dotenv

  3. Запустите бота:
       python {result['output_file']}
{_sep}""")


# ===========================================================================
# Точка входа
# ===========================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Использование : python script.py \"Страна, Компания, сайт\"\n"
            "Пример        : python script.py "
            "\"ОАЭ, Aquiline International Corporation, www.aquiline-aero.com\""
        )
        sys.exit(1)

    run_pipeline(sys.argv[1])
