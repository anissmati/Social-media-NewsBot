from telegram import Update
from telegram.ext import ContextTypes
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from database.user_service import create_user, user_exists, init_database

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = update.effective_user.id
    init_database()

    if not user_exists(user_id):
        create_user(user_id)
    

    text = (f"Welcome {user.first_name}\n\n"
            "The available commands:\n"
            "Search for News: /FindNews\n"
            "Modefy settings: /Settings\n"
            "Check your credits: /credits")
    
    await update.message.reply_text(text)
    