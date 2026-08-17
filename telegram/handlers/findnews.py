import glob
import os
import shutil
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

sys.modules["nltk.inisec"] = type("mock", (object,), {"find_spec": lambda *args, **kwargs: None})

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from Searcher.main import run_pipeline_1
from content.main import run_pipeline_2
from database.articles_db import get_article, get_articles
from database.user_service import get_user_settings, update_settings


CATEGORIES = {
    "Technology": "tech",
    "Sports": "sports",
    "Politics": "politics",
    "Science": "science",
    "Business": "business",
    "World": "world",
}

CALLBACK_FIND_PREFIX = "findnews:"
CALLBACK_CREATE_PREFIX = "create:"


def _build_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(label, callback_data=f"{CALLBACK_FIND_PREFIX}{value}")
        for label, value in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


async def findnews(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Choose a news category:", reply_markup=_build_keyboard())


async def findnews_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and present articles belonging only to the requesting Telegram user."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    if get_user_settings(user_id)["credit"] < 20:
        await query.message.reply_text("Sorry you don't have enough credits!")
        return

    category = query.data.removeprefix(CALLBACK_FIND_PREFIX)
    await query.edit_message_text(f"Searching news for: {category} ...")

    user_id = update.effective_user.id
    run_pipeline_1(category, user_id)
    articles = get_articles(user_id)

    for slot, article in enumerate(articles, start=1):
        title = article.title or "No Title"
        text = f"<b>Article {slot:02d}</b>\n<blockquote>{title}</blockquote>"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Create Post", callback_data=f"{CALLBACK_CREATE_PREFIX}{slot}")]]
        )
        await query.message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def handle_create_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    user_credit = get_user_settings(user_id)["credit"]

    if user_credit < 20:
        await query.message.reply_text("Sorry you don't have enough credits!")
        return

    update_settings.credit(user_id, (user_credit - 20))

    slot = int(query.data.removeprefix(CALLBACK_CREATE_PREFIX))
    article = get_article(user_id, slot)
    if article is None:
        await query.message.reply_text("This article is no longer available. Please fetch news again.")
        return

    await query.message.reply_text(f"Generating post for article #{slot}...")
    run_pipeline_2(slot, user_id, article)

    base_dir = "output"
    all_folders = [
        os.path.join(base_dir, directory)
        for directory in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, directory))
    ]
    if not all_folders:
        await query.message.reply_text("Error: Couldn't find the output directory.")
        return

    latest_folder = max(all_folders, key=os.path.getmtime)
    jpg_files = glob.glob(os.path.join(latest_folder, "*.jpg"))
    txt_files = glob.glob(os.path.join(latest_folder, "*.txt"))
    if not jpg_files or not txt_files:
        await query.message.reply_text("Error: Generated files were not found in the output folder.")
        return

    try:
        with open(txt_files[0], "r", encoding="utf-8") as file:
            caption_text = file.read()
        with open(jpg_files[0], "rb") as photo:
            await query.message.reply_photo(photo=photo, caption=caption_text[:1024])
        if len(caption_text) > 1024:
            await query.message.reply_text(f"Full description:\n\n{caption_text}")
    finally:
        shutil.rmtree(latest_folder, ignore_errors=True)
