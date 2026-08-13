import sys, os, re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.user_service import get_user_settings, update_settings, reset_settings
from database.conversion import gradient_tuple_to_hex, hex_to_gradient_tuple
from database.settings import *

HEX_COLOR_PATTERN = re.compile(r"^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
WAITING_FOR_TEXT_HEX = 1
WAITING_FOR_GRADIENT_HEX = 2
CALLBACK_EDIT_MARKUP = "setting:"
EDIT_PLATFORM_MARKUP = "platform:"
EDIT_TONE_MARKUP = "tone:"
EDIT_LANGUAGE_MARKUP = "language:"

def filter_settings(settings):
    return {k: settings[k] for k in list(settings)[:5]}

def _build_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(f"{label}", callback_data=f"{CALLBACK_EDIT_MARKUP}{value}")
        for label, value in SETTING.items()
    ]
    rows = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]
    return InlineKeyboardMarkup(rows)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    user_settings = get_user_settings(user_id)

    text = "<b>Current settings:</b>\n\n"
    for label, value in filter_settings(SETTING).items():
        if label == "Gradient Color":
            text = text + f"<b>{label}</b>: {gradient_tuple_to_hex(user_settings[value])}\n" 
        else:
            text = text + f"<b>{label}</b>: {user_settings[value]}\n"
        
    await update.message.reply_text(
        text = f"{text}\n""Choose to edit:",
        parse_mode= ParseMode.HTML,
        reply_markup= _build_keyboard()
    )

#EDIT THE TEXT COLOR
async def edit_text_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "Please send a color in hex format (e.g., `#FF5733` or `FFF`)."
    )
    return WAITING_FOR_TEXT_HEX

async def handle_text_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if HEX_COLOR_PATTERN.match(user_text):
        normalized_hex = user_text if user_text.startswith("#") else f"#{user_text}"

        update_settings.text_color(user_id, normalized_hex)
        await update.message.reply_text(
            f"Success! Text Color changed to: `{normalized_hex}`", parse_mode="Markdown"
        )
        return ConversationHandler.END
        
    else:
        await update.message.reply_text(
            "❌ Invalid hex format. Please try again and send a valid hex color (e.g., `#FF5733`)."
        )
        return WAITING_FOR_TEXT_HEX

#EDIT THE GRADIENT COLOR
async def edit_gradient_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "Please send a color in hex format (e.g., `#FF5733` or `FFF`)."
    )
    return WAITING_FOR_GRADIENT_HEX

async def handle_gradient_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if HEX_COLOR_PATTERN.match(user_text):
        normalized_hex = user_text if user_text.startswith("#") else f"#{user_text}"
        final = hex_to_gradient_tuple(normalized_hex)

        update_settings.gradient_color(user_id, final)
        await update.message.reply_text(
            f"Success! Grandiant Color changed to: `{normalized_hex}`", parse_mode="Markdown"
        )
        return ConversationHandler.END
        
    else:
        await update.message.reply_text(
            "❌ Invalid hex format. Please try again and send a valid hex color (e.g., `#FF5733`)."
        )
        return WAITING_FOR_GRADIENT_HEX

#EDIT PLATFORM
def _build_platform_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(f"{label}", callback_data=f"{EDIT_PLATFORM_MARKUP}{value}")
        for label, value in PLATFORMS.items()
    ]
    rows = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]
    return InlineKeyboardMarkup(rows)

async def edit_platform_choices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "<b>Choose the new platform: </b>",
        reply_markup= _build_platform_keyboard(),
        parse_mode= ParseMode.HTML
    )

async def edit_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    platform = query.data.removeprefix(EDIT_PLATFORM_MARKUP)
    update_settings.platform(user_id, platform)

    await query.message.reply_text(f"Platform changed succesfully to: {platform}")
    await query.message.delete()

#EDIT TONE
def _build_tone_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(f"{label}", callback_data=f"{EDIT_TONE_MARKUP}{value}")
        for label, value in TONES.items()
    ]
    rows = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]
    return InlineKeyboardMarkup(rows)

async def edit_tone_choices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "<b>Choose the new tone: </b>",
        reply_markup= _build_tone_keyboard(),
        parse_mode= ParseMode.HTML
    )

async def edit_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    tone = query.data.removeprefix(EDIT_TONE_MARKUP)
    update_settings.tone(user_id, tone)

    await query.message.reply_text(f"Tone changed succesfully to: {tone}")
    await query.message.delete()

#EDIT LANGUAGE
def _build_language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(f"{label}", callback_data=f"{EDIT_LANGUAGE_MARKUP}{value}")
        for label, value in LANGUAGES.items()
    ]
    rows = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]
    return InlineKeyboardMarkup(rows)

async def edit_language_choices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "<b>Choose the new language: </b>",
        reply_markup= _build_language_keyboard(),
        parse_mode= ParseMode.HTML
    )

async def edit_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    tone = query.data.removeprefix(EDIT_LANGUAGE_MARKUP)
    update_settings.language(user_id, tone)

    await query.message.reply_text(f"Language changed succesfully to: {tone}")
    await query.message.delete()

#RESET SETTINGS
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    reset_settings(user_id)
    await query.message.reply_text("User settings succesfully reseted to default!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled color editing.")
    return ConversationHandler.END