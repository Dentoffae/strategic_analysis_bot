#!/usr/bin/env python3
import os
import asyncio
import time
from typing import List

from dotenv import load_dotenv

# aiogram 3.x
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# LangChain (современные импорты)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрируем шрифт с поддержкой кириллицы.
# Приоритет: Arial (Windows) → DejaVuSans (Linux/macOS) → Helvetica (fallback без кириллицы).
_FONT_REGULAR = "Helvetica"
_FONT_BOLD    = "Helvetica-Bold"

def _try_register(name: str, path: str) -> bool:
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    except Exception:
        return False

_FONT_CANDIDATES = [
    ("ArialCyr",     "ArialCyrBold",     "C:/Windows/Fonts/arial.ttf",     "C:/Windows/Fonts/arialbd.ttf"),
    ("DejaVuSans",   "DejaVuSans-Bold",  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("DejaVuSans",   "DejaVuSans-Bold",  "/Library/Fonts/DejaVuSans.ttf", "/Library/Fonts/DejaVuSans-Bold.ttf"),
]

for _reg, _bold, _reg_path, _bold_path in _FONT_CANDIDATES:
    if _try_register(_reg, _reg_path):
        _try_register(_bold, _bold_path)
        _FONT_REGULAR, _FONT_BOLD = _reg, _bold
        break

# ---------------------------------------------------------------------------
load_dotenv()

BOT_TOKEN    = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не задан в .env")

bot    = Bot(token=BOT_TOKEN)
router = Router()

llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0.3,
    api_key=OPENAI_API_KEY,
    base_url=os.getenv("OPENAI_BASE_URL") or None,
)

# Хранилище последних PDF по user_id
user_reports: dict[int, str] = {}

# ---------------------------------------------------------------------------
# FSM состояния
# ---------------------------------------------------------------------------

class AnalysisForm(StatesGroup):
    waiting_input = State()
    processing    = State()

# ---------------------------------------------------------------------------
# LangChain цепочки стратегического анализа
# ---------------------------------------------------------------------------

swot_chain = (
    ChatPromptTemplate.from_messages([
        ("system", (
            "Ты эксперт по стратегическому менеджменту. Проведи подробный SWOT-анализ компании.\n"
            "Структура ответа (минимум 400 слов):\n"
            "💪 СИЛЬНЫЕ СТОРОНЫ (Strengths) — внутренние конкурентные преимущества\n"
            "⚠️ СЛАБЫЕ СТОРОНЫ (Weaknesses) — внутренние ограничения и недостатки\n"
            "🚀 ВОЗМОЖНОСТИ (Opportunities) — внешние факторы для роста\n"
            "🔴 УГРОЗЫ (Threats) — внешние риски и вызовы\n"
            "Учитывай страну, отрасль и специфику компании. Отвечай на русском языке."
        )),
        ("human", "Компания: {company_name}. Отрасль: {industry}. Страна: {country}. Сайт: {website}."),
    ])
    | llm
    | StrOutputParser()
)

pestel_chain = (
    ChatPromptTemplate.from_messages([
        ("system", (
            "Ты эксперт по стратегическому менеджменту. Проведи подробный PESTEL-анализ компании.\n"
            "Структура ответа (минимум 400 слов):\n"
            "🏛 Политические факторы (Political)\n"
            "💰 Экономические факторы (Economic)\n"
            "👥 Социальные факторы (Social)\n"
            "💡 Технологические факторы (Technological)\n"
            "🌿 Экологические факторы (Environmental)\n"
            "⚖️ Правовые факторы (Legal)\n"
            "Учитывай страну операций и отрасль. Отвечай на русском языке."
        )),
        ("human", "Компания: {company_name}. Отрасль: {industry}. Страна: {country}. Сайт: {website}."),
    ])
    | llm
    | StrOutputParser()
)

porter_chain = (
    ChatPromptTemplate.from_messages([
        ("system", (
            "Ты эксперт по стратегическому менеджменту. Проведи анализ по модели Пяти сил Портера.\n"
            "Структура ответа (минимум 400 слов):\n"
            "⚔️ Конкурентное соперничество — интенсивность конкуренции в отрасли\n"
            "🏭 Власть поставщиков — переговорная сила поставщиков\n"
            "🛒 Власть покупателей — переговорная сила клиентов\n"
            "🔄 Угроза субститутов — риск замены продукта\n"
            "🚪 Угроза новых игроков — барьеры для входа в отрасль\n"
            "Дай итоговую оценку конкурентной привлекательности отрасли. Отвечай на русском языке."
        )),
        ("human", "Компания: {company_name}. Отрасль: {industry}. Страна: {country}. Сайт: {website}."),
    ])
    | llm
    | StrOutputParser()
)

ansoff_chain = (
    ChatPromptTemplate.from_messages([
        ("system", (
            "Ты эксперт по стратегическому менеджменту. Проведи анализ по матрице Ансоффа.\n"
            "Структура ответа (минимум 400 слов):\n"
            "📍 Проникновение на рынок — рост на существующих рынках с текущим продуктом\n"
            "🌍 Развитие рынка — выход на новые рынки с текущим продуктом\n"
            "🔧 Развитие продукта — новые продукты для существующих рынков\n"
            "🚀 Диверсификация — новые продукты на новых рынках\n"
            "Рекомендуй оптимальную стратегию роста с обоснованием. Отвечай на русском языке."
        )),
        ("human", "Компания: {company_name}. Отрасль: {industry}. Страна: {country}. Сайт: {website}."),
    ])
    | llm
    | StrOutputParser()
)

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def split_message(text: str, limit: int = 4000) -> List[str]:
    """Разбивает текст на части ≤ limit символов по границам строк."""
    if len(text) <= limit:
        return [text]
    parts, current = [], ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit:
            if current:
                parts.append(current)
            current = line
        else:
            current += line
    if current:
        parts.append(current)
    return parts


def transliterate(text: str) -> str:
    """Транслитерирует кириллицу в латиницу для PDF (Helvetica не поддерживает UTF-8)."""
    tbl = {
        'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z',
        'И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R',
        'С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh',
        'Щ':'Shch','Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya',
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
        'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
        'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh',
        'щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    }
    return ''.join(tbl.get(ch, ch) for ch in text)


def generate_pdf(company: str, swot: str, pestel: str, porter: str, ansoff: str) -> str:
    """Генерирует PDF-отчёт с кириллицей через зарегистрированный TTF-шрифт."""
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"report_{int(time.time())}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    page_w, page_h = A4
    margin = 50
    max_chars = int((page_w - 2 * margin) / 5.5)  # ~90 символов на строку при 10pt
    y = page_h - margin
    line_h = 15

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont(_FONT_REGULAR, 10)
        y = page_h - margin

    def draw_line(text: str, font: str = None, size: int = 10, gap: int = 0):
        nonlocal y
        if y < margin + line_h:
            new_page()
        c.setFont(font or _FONT_REGULAR, size)
        # Убираем markdown-звёздочки и символы которые не в шрифте
        clean = text.replace("**", "").replace("*", "").replace("■", "•")
        c.drawString(margin, y, clean[:max_chars])
        y -= line_h + gap

    def draw_section(title: str, body: str):
        draw_line("", gap=4)
        draw_line(title, font=_FONT_BOLD, size=12, gap=3)
        for raw_line in body.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                y_ref = y  # пропускаем пустые строки компактно
                continue
            for chunk in split_message(stripped, limit=max_chars):
                draw_line(chunk)

    # Заголовок документа
    draw_line(f"Стратегический анализ: {company}", font=_FONT_BOLD, size=14, gap=6)
    draw_line(f"Дата: {time.strftime('%d.%m.%Y')}", size=9, gap=10)

    draw_section("SWOT-анализ", swot)
    draw_section("PESTEL-анализ", pestel)
    draw_section("Пять сил Портера", porter)
    draw_section("Матрица Ансоффа", ansoff)

    c.save()
    return filename

# ---------------------------------------------------------------------------
# Обработчики команд
# ---------------------------------------------------------------------------

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Добро пожаловать в бот стратегического анализа!</b>\n\n"
        "Я проведу полный анализ любой компании:\n"
        "• SWOT-анализ\n"
        "• PESTEL-анализ\n"
        "• Пять сил Портера\n"
        "• Матрица Ансоффа\n\n"
        "Команды:\n"
        "/analyze — запустить анализ\n"
        "/pdf     — получить последний отчёт PDF\n"
        "/help    — справка",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Справка</b>\n\n"
        "/analyze — введите данные о компании для анализа\n"
        "/pdf     — получить последний сформированный PDF-отчёт\n"
        "/start   — приветствие\n\n"
        "<i>Формат ввода:</i> Страна, Название компании, Сайт\n"
        "<i>Пример:</i> ОАЭ, Aquiline International, www.aquiline-aero.com",
        parse_mode="HTML",
    )


@router.message(Command("analyze"))
async def cmd_analyze(message: Message, state: FSMContext) -> None:
    await message.answer(
        "🔍 Введите данные о компании в формате:\n"
        "<b>Страна, Название компании, Сайт или соцсеть</b>\n\n"
        "Пример: ОАЭ, Aquiline International Corporation, www.aquiline-aero.com",
        parse_mode="HTML",
    )
    await state.set_state(AnalysisForm.waiting_input)


@router.message(Command("pdf"))
async def cmd_pdf(message: Message) -> None:
    path = user_reports.get(message.from_user.id)
    if path and os.path.exists(path):
        await message.answer_document(FSInputFile(path), caption="📄 Ваш стратегический отчёт")
    else:
        await message.answer("⚠️ Отчёт не найден. Сначала выполните /analyze.")


@router.message(AnalysisForm.waiting_input)
async def process_company_input(message: Message, state: FSMContext) -> None:
    """Парсит ввод пользователя, запускает 4 цепочки анализа, отправляет результат."""
    raw = message.text.strip()
    parts = [p.strip() for p in raw.split(",", 2)]
    country  = parts[0] if len(parts) > 0 else "Неизвестно"
    company  = parts[1] if len(parts) > 1 else raw
    website  = parts[2] if len(parts) > 2 else "—"
    industry = "общая отрасль"  # можно расширить через доп. вопрос

    await state.set_state(AnalysisForm.processing)
    await message.answer(f"⏳ Анализирую <b>{company}</b>. Это займёт около минуты…", parse_mode="HTML")

    params = {"company_name": company, "industry": industry, "country": country, "website": website}

    try:
        swot   = await swot_chain.ainvoke(params)
        pestel = await pestel_chain.ainvoke(params)
        porter = await porter_chain.ainvoke(params)
        ansoff = await ansoff_chain.ainvoke(params)
    except Exception as exc:
        await message.answer(f"❌ Ошибка при обращении к AI: {exc}\nПопробуйте позже.")
        await state.clear()
        return

    # Отправляем результаты по секциям, разбивая длинные сообщения
    sections = [
        ("📊 <b>SWOT-анализ</b>",         swot),
        ("🌐 <b>PESTEL-анализ</b>",        pestel),
        ("⚔️ <b>Пять сил Портера</b>",     porter),
        ("🚀 <b>Матрица Ансоффа</b>",      ansoff),
    ]
    for header, body in sections:
        await message.answer(header, parse_mode="HTML")
        for chunk in split_message(body):
            await message.answer(chunk)

    # Генерируем PDF
    try:
        pdf_path = generate_pdf(company, swot, pestel, porter, ansoff)
        user_reports[message.from_user.id] = pdf_path
        await message.answer_document(
            FSInputFile(pdf_path),
            caption="📄 Полный стратегический отчёт в PDF",
        )
    except Exception as exc:
        await message.answer(f"⚠️ PDF не удалось создать: {exc}\nТекстовый анализ выше сохранён.")

    await state.clear()

# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

async def main() -> None:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
