from telegram.ext import ApplicationBuilder, CommandHandler,CallbackQueryHandler, MessageHandler, filters
from handlers.start import start
from handlers.findnews import *
from handlers.settings import *
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("findnews", findnews))
    app.add_handler(
        CallbackQueryHandler(findnews_callback, pattern=f"^{CALLBACK_FIND_PREFIX}")
    )
    app.add_handler(
            CallbackQueryHandler(handle_create_post, pattern=f"^{CALLBACK_CREATE_PREFIX}")
        )
    app.add_handler(CommandHandler("settings", settings))
    #UPDATE TEXT COLOR HANDLER
    text_color_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_text_color, pattern=f"^{CALLBACK_EDIT_MARKUP}text_color")
        ],
        states={
            WAITING_FOR_TEXT_HEX: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_color)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(text_color_conv_handler)

    #UPDATE GRADIENT COLOR HANDLER
    gradient_color_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(edit_gradient_color, pattern=f"^{CALLBACK_EDIT_MARKUP}gradient_color")
            ],
            states={
                WAITING_FOR_GRADIENT_HEX: [
                    MessageHandler(filters.TEXT & (~filters.COMMAND), handle_gradient_color)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    app.add_handler(gradient_color_conv_handler)

    #UPDATE PLATFORM
    app.add_handler(
        CallbackQueryHandler(edit_platform_choices, pattern=f"^{CALLBACK_EDIT_MARKUP}platform")
    )
    app.add_handler(
        CallbackQueryHandler(edit_platform, pattern=f"^{EDIT_PLATFORM_MARKUP}")
    )

    #EDIT TONE
    app.add_handler(
        CallbackQueryHandler(edit_tone_choices, pattern=f"^{CALLBACK_EDIT_MARKUP}tone")
    )
    app.add_handler(
        CallbackQueryHandler(edit_tone, pattern=f"^{EDIT_TONE_MARKUP}")
    )

    #EDIT TONE
    app.add_handler(
        CallbackQueryHandler(edit_language_choices, pattern=f"^{CALLBACK_EDIT_MARKUP}language")
    )
    app.add_handler(
        CallbackQueryHandler(edit_language, pattern=f"^{EDIT_LANGUAGE_MARKUP}")
    )

    #RESET SETTINGS
    app.add_handler(
        CallbackQueryHandler(reset, pattern=f"^{CALLBACK_EDIT_MARKUP}reset")
    )
    
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()