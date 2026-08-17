import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database.user_service import get_user_settings, update_settings

CREDIT_MARKUP = "credit"

BUNDLES = {
    50: 25,
    100: 45,
    150: 65,
    200: 80,
    250: 95
}

async def credit(update: Update, context: ContextTypes) -> None:
    user_id = update.effective_user.id
    user_credits = get_user_settings(user_id)["credit"]

    keyboard = []
    for credits, stars in BUNDLES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"✨ {credits} Credits — {stars} Stars",
                callback_data=f"buy_{credits}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text =f"<b>Your available credits: </b> {user_credits}\n \nPurchase more credits:"
           

    await update.message.reply_text(text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

#send the invoice
async def buy_credit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("buy_"):
        return

    # Extract credit amount from callback data (e.g., "buy_100" -> 100)
    credits_amount = int(query.data.split("_")[1])
    stars_price = BUNDLES.get(credits_amount)

    if not stars_price:
        await query.message.reply_text("❌ Invalid bundle selected.")
        return

    title = f"{credits_amount} Bot Credits"
    description = f"Purchase {credits_amount} credits to use within the bot."
    payload = f"credits_{credits_amount}"  # Dynamic payload to track verification later
    currency = "XTR"
    prices = [LabeledPrice(f"{credits_amount} Credits", stars_price)]

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Must be empty string for Telegram Stars
        currency=currency,
        prices=prices,
        start_parameter="buy-credits"
    )

#pre checkout
async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    
    # Verify the payload starts with our expected prefix
    if query.invoice_payload.startswith("credits_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong with your order.")

#succesful payment
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    
    if payment.currency == "XTR" and payment.invoice_payload.startswith("credits_"):
        # Extract the credit amount safely from the payload string
        credits_to_add = int(payment.invoice_payload.split("_")[1])
        current_credits = get_user_settings(user_id)["credit"]
        
        # Update user balance in database
        update_settings.credit(user_id, current_credits + credits_to_add)
        
        await update.message.reply_text(
            f"✅ **Payment Successful!**\n\n"
            f"Successfully added **{credits_to_add} credits** to your account. Enjoy!"
        )