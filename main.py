import asyncio
import aiohttp
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import sys
from config import BOT_TOKEN

TOKEN = BOT_TOKEN
CSV_PATH = "data.csv"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ------------------- Глобальные переменные -------------------

_df = None  # кэш таблицы

# хранение информации о пользователях
# {user_id: {"mode":"category"/"text", "candidates":[], "pos":int, "shown":set(), "column":str}}
users = {}

# сопоставление подкатегорий на английском с их переводом на русский
SUBCATEGORY_MAP = {
    "humour": {
        "Несмешной": "not_funny",
        "Смешной": "funny",
        "Очень смешной": "very_funny",
        "Уморительный": "hilarious"
    },
    "sarcasm": {
        "Без сарказма": "not_sarcastic",
        "Обычный": "general",
        "Двусмысленный": "twisted_meaning",
        "Очень двусмысленный": "very_twisted"
    },
    "offensive": {
        "Без оскорбления": "not_offensive",
        "Слегка обидный": "slight",
        "Очень обидный": "very_offensive",
        "Крайне обидный": "hateful_offensive"
    },
    "motivational": {
        "Обычный": "not_motivational",
        "Мотивирующий": "motivational"
    },
    "overall_sentiment": {
        "Очень негативный": "very_negative",
        "Негативный": "negative",
        "Нейтральный": "neutral",
        "Позитивный": "positive",
        "Очень позитивный": "very_positive"
    }
}

# названия столбцов, которые должны содержаться в таблице
REQUIRED_COLS = {'image_name', 'original_name', 'image_url', 'text_ocr', 'text_corrected',
                 'humour', 'sarcasm', 'offensive', 'motivational', 'overall_sentiment'}


# ------------------- Создание кнопок -------------------

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск по категориям"), KeyboardButton(text="Поиск по словам")],
            [KeyboardButton(text="🔁 Начать сначала"), KeyboardButton(text="❌ Выйти")]
        ],
        resize_keyboard=True
    )


def category_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Юмор"), KeyboardButton(text="Сарказм")],
            [KeyboardButton(text="Оскорбление"), KeyboardButton(text="Мотивация")],
            [KeyboardButton(text="Общее настроение"), KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )


def action_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующий мем"), KeyboardButton(text="Новый поиск")],
            [KeyboardButton(text="Показать показанные мемы"), KeyboardButton(text="🔁 Начать сначала")],
            [KeyboardButton(text="❌ Выйти")]
        ],
        resize_keyboard=True
    )


def subcategory_kb(col):
    mapping = SUBCATEGORY_MAP.get(col, {})
    buttons = [[KeyboardButton(text=k)] for k in mapping.keys()]
    buttons.append([KeyboardButton(text="Назад"), KeyboardButton(text="🔁 Начать сначала")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# ------------------- Загрузка данных -------------------

async def load_df():
    global _df
    if _df is not None:
        return _df
    try:
        df = pd.read_csv(CSV_PATH)
        if not REQUIRED_COLS.issubset(set(df.columns)):
            missing = REQUIRED_COLS - set(df.columns)
            raise RuntimeError(f"Отсутствуют колонки: {', '.join(missing)}")
        _df = df
        return _df
    except Exception as e:
        print("Ошибка загрузки data.csv:", e)
        sys.exit(1)


# ------------------- Проверка URL -------------------

async def url_ok(session, url, timeout=5):
    try:
        async with session.head(url, allow_redirects=True, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:
        try:
            async with session.get(url, allow_redirects=True, timeout=timeout) as r2:
                return 200 <= r2.status < 300
        except Exception:
            return False


# ------------------- Отправка мемов пользователю -------------------

async def safe_send_photo(chat_id, url, caption=None, reply_markup=None):
    try:
        await bot.send_photo(chat_id, url, caption=caption, reply_markup=reply_markup)
        return True
    except Exception:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=8) as r:
                    if r.status == 200:
                        data = await r.read()
                        await bot.send_photo(chat_id, data, caption=caption, reply_markup=reply_markup)
                        return True
        except Exception:
            return False
    return False


# ------------------- Поиск следующего мемa -------------------

async def find_next_available(session, candidates, pos, shown_set):
    n = len(candidates)
    i = pos
    while i < n:
        row = candidates[i]
        url = str(row.get("image_url", "")).strip()
        if url and url not in shown_set:
            ok = await url_ok(session, url)
            if ok:
                return i, row
        i += 1
    return None, None


async def send_next_meme(uid: int, msg: types.Message):
    state = users.get(uid)
    if not state or not state.get("candidates"):
        await msg.answer("Сначала начните поиск (/start).", reply_markup=main_kb())
        return
    async with aiohttp.ClientSession() as session:
        i, row = await find_next_available(session, state["candidates"], state["pos"], state["shown"])
        if row is None:
            await msg.answer("Больше доступных мемов не найдено.", reply_markup=main_kb())
            return
        url = str(row.get("image_url", "")).strip()
        caption = row.get("text_corrected", "") or row.get("text_ocr", "")
        sent = await safe_send_photo(msg.chat.id, url, caption=caption, reply_markup=action_kb())
        if sent:
            state["shown"].add(url)
            state["pos"] = i + 1
        else:
            await msg.answer("Не удалось отправить мем.", reply_markup=action_kb())


# ------------------- Команды -------------------

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await load_df()
    uid = msg.from_user.id
    users[uid] = {"mode": None, "candidates": [], "pos": 0, "shown": set()}
    await msg.answer("Выберите способ поиска мемов:", reply_markup=main_kb())


@dp.message(lambda m: m.text == "❌ Выйти")
async def cmd_exit(msg: types.Message):
    uid = msg.from_user.id
    users.pop(uid, None)
    await msg.answer("Ок. Чтобы начать снова, /start", reply_markup=ReplyKeyboardRemove())


@dp.message(lambda m: m.text in ["🔁 Начать сначала", "Новый поиск"])
async def cmd_restart(msg: types.Message):
    await cmd_start(msg)


@dp.message(lambda m: m.text == "Поиск по категориям")
async def mode_category(msg: types.Message):
    await msg.answer("Выберите категорию:", reply_markup=category_kb())


@dp.message(lambda m: m.text == "Поиск по словам")
async def mode_text(msg: types.Message):
    uid = msg.from_user.id
    users.setdefault(uid, {"mode": None, "candidates": [], "pos": 0, "shown": set()})
    users[uid]["mode"] = "text"
    await msg.answer("Введи слово или фразу для поиска:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔁 Начать сначала"), KeyboardButton(text="❌ Выйти")]], resize_keyboard=True))


@dp.message(lambda m: m.text in ["Юмор", "Сарказм", "Оскорбление", "Мотивация", "Общее настроение"])
async def choose_main_category(msg: types.Message):
    mapping = {
        "Юмор": "humour",
        "Сарказм": "sarcasm",
        "Оскорбление": "offensive",
        "Мотивация": "motivational",
        "Общее настроение": "overall_sentiment"
    }
    col = mapping[msg.text]
    uid = msg.from_user.id
    users.setdefault(uid, {"mode": None, "candidates": [], "pos": 0, "shown": set()})
    users[uid]["mode"] = "category"
    users[uid]["column"] = col
    if col in SUBCATEGORY_MAP:
        await msg.answer("Выбери подкатегорию:", reply_markup=subcategory_kb(col))
    else:
        await msg.answer("Начинаю поиск...", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]],
                                                                              resize_keyboard=True))


# ------------------- Главный хэндлер -------------------

@dp.message()
async def main_handler(msg: types.Message):
    uid = msg.from_user.id
    text = msg.text.strip()
    state = users.get(uid)
    df = await load_df()

    # кнопки действий
    if text == "Следующий мем":
        await send_next_meme(uid, msg)
        return

    if text == "Показать показанные мемы":
        shown = state.get("shown", set()) if state else set()
        if not shown:
            await msg.answer("Пока ничего не показано.", reply_markup=main_kb())
            return
        for url in list(shown)[-10:]:
            await safe_send_photo(msg.chat.id, url)
        await msg.answer("Это последние показанные мемы.", reply_markup=action_kb())
        return

    if text == "Назад":
        await msg.answer("Выберите категорию:", reply_markup=category_kb())
        return

    # ---------------- Поиск по тексту ----------------
    if state and state.get("mode") == "text":
        query = text.lower()
        rows = []
        for r in df.to_dict(orient="records"):
            txt = f"{r.get('text_ocr', '')} {r.get('text_corrected', '')}".lower()
            if query in txt:
                url = str(r.get("image_url", "")).strip()
                if url and url not in state["shown"]:
                    rows.append(r)
        if not rows:
            await msg.answer("По данным словам ничего не найдено.", reply_markup=main_kb())
            return
        state["candidates"] = rows
        state["pos"] = 0
        await send_next_meme(uid, msg)
        return

    # ---------------- Поиск по категориям ----------------
    if state and state.get("mode") == "category" and state.get("column"):
        col = state["column"]
        mapped = SUBCATEGORY_MAP.get(col, {}).get(text)
        if mapped is None:
            await msg.answer("Не распознал подкатегорию. Выбери из списка.", reply_markup=subcategory_kb(col))
            return
        candidates_df = df[df[col].astype(str).str.lower() == str(mapped).lower()]
        rows = [r for r in candidates_df.to_dict(orient="records") if
                str(r.get("image_url", "")).strip() not in state["shown"]]
        if not rows:
            await msg.answer("По этой подкатегории ничего доступного не найдено.", reply_markup=main_kb())
            return
        state["candidates"] = rows
        state["pos"] = 0
        await send_next_meme(uid, msg)
        return

    await msg.answer("Не понял. Выбери режим.", reply_markup=main_kb())


# ------------------- Запуск -------------------

if __name__ == "__main__":
    try:
        print("Bot started")
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        print("Stopped by user")
        sys.exit(0)
