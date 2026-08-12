from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import sys, os, json, glob
sys.modules['nltk.inisec'] = type('mock', (object,), {'find_spec': lambda *args, **kwargs: None})

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Searcher.main import run_pipeline_1
from content.main import run_pipeline_2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Dynamic path to data file
json_path = os.path.join(PROJECT_ROOT, "data", "articles.json")

# category label -> callback_data value
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
    # 2 buttons per row
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)

async def findnews(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Choose a news category:",
        reply_markup=_build_keyboard(),
    )


async def findnews_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the button press from the /findnews menu."""
    query = update.callback_query
    await query.answer()  # stop the Telegram loading spinner

    category = query.data.removeprefix(CALLBACK_FIND_PREFIX)
    await query.edit_message_text(f"Searching news for: {category} ...")

    run_pipeline_1(category)
    with open(json_path, "r", encoding="utf-8") as file:
        articles = json.load(file)

    for index, article in enumerate(articles):
        title = (article.get('title', 'No Title'))
        title = (f"<b>Article 0{index + 1}</b>\n"
                 f"<blockquote>{title}</blockquote>")
        
        # Create an Inline Keyboard with the "Create Post" button
        # Pass a unique callback_data (e.g., using index or article ID) to identify which article was clicked
        keyboard = [
            [InlineKeyboardButton("Create Post✨", callback_data=f"{CALLBACK_CREATE_PREFIX}{index}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send separate message for each article
        await query.message.reply_text(
            text=title,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    


async def handle_create_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()  # Acknowledge button click

    # Extract the index from callback_data ("create_post_0" -> index 0)
    article_index = int(query.data.removeprefix(CALLBACK_CREATE_PREFIX))
    target_index = article_index + 1  # 1-based index for your pipeline

    await query.message.reply_text(f"⏳ Generating post for article #{target_index}...")

    # 1. Run your pipeline
    run_pipeline_2(target_index, user_id)

    # 2. Find the newest folder matching "YYYY-MM-DD_HH-MM-SS" pattern
    base_dir = "output"  
    # Get all directories and find the most recently created one
    all_folders = [
        os.path.join(base_dir, d) for d in os.listdir(base_dir) 
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    
    if not all_folders:
        await query.message.reply_text("❌ Error: Couldn't find the output directory.")
        return

    latest_folder = max(all_folders, key=os.path.getmtime)

    # 3. Locate the .jpg image and .txt description file inside that folder
    jpg_files = glob.glob(os.path.join(latest_folder, "*.jpg"))
    txt_files = glob.glob(os.path.join(latest_folder, "*.txt"))

    if not jpg_files or not txt_files:
        await query.message.reply_text("❌ Error: Generated files were not found in the output folder.")
        return

    image_path = jpg_files[0]
    description_path = txt_files[0]

    # Read the text description content
    with open(description_path, "r", encoding="utf-8") as f:
        caption_text = f.read()

    # 4. Send image with description caption (or as separate document/photo)
    with open(image_path, "rb") as photo:
        await query.message.reply_photo(
            photo=photo,
            caption=caption_text[:1024]  
        )

    if len(caption_text) > 1024:
        await query.message.reply_text(f"📝 Full Description:\n\n{caption_text}")