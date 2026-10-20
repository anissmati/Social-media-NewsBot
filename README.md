# NewsBot

NewsBot discovers news stories from NewsAPI and GNews, scores and ranks them with the project's trained model, and turns a selected story into a social media image and caption using Google Gemini. You can use it through a personal Telegram bot or run the included browser interface locally.

## Features

- Search news by category and rank articles with the bundled scoring model.
- Generate a social media title, description, and image for an article.
- Personalize the platform, language, tone, text color, and image gradient.
- Store each user's settings, credits, and current articles in a local SQLite database.
- Use the Telegram bot or the local Flask web interface.

## Requirements

- Python 3.14.6 (the version declared by this project in `.python-version`).
- API credentials for Google Gemini, NewsAPI, and GNews.
- A Telegram bot token if you plan to run your own Telegram bot.

The trained model is included at `models/scoring_model.pkl`. You do not need to train or export it to run the application.

## 1. Download and install

Clone or download this project, then open a terminal in the project folder.

### Windows PowerShell

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents environment activation, invoke the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure API credentials

Copy `.env.example` to `.env` in the project root, then fill in the values:

```dotenv
GEMINI_API_KEY=your_google_gemini_api_key
NEWSAPI_KEY=your_newsapi_key
GNEWS_KEY=your_gnews_key
BOT_TOKEN=your_telegram_bot_token
```

Get a Gemini key from [Google AI Studio](https://aistudio.google.com/), NewsAPI and GNews keys from their respective services, and a Telegram bot token from [@BotFather](https://t.me/BotFather). Keep `.env` private; do not commit or share API keys or bot tokens. `BOT_TOKEN` is only needed for the Telegram option. News search requires working NewsAPI and GNews keys, while generating captions requires a Gemini key.

## Run your personal Telegram bot

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token into `BOT_TOKEN` in `.env`.
2. Make sure the API keys above are configured.
3. From the project root, start the bot:

   ```powershell
   python telegram/main.py
   ```

   On macOS or Linux, use the same command from the activated virtual environment.

4. Open your bot in Telegram and send `/start`. Use `/findnews` to search, `/settings` to customize posts, and `/credits` to view your credits.

Keep the process running while you use the bot. This starts a bot that you own and operate; it is separate from the hosted bot link below.

## Run the browser interface locally

1. Configure the API keys in `.env` as described above. A Telegram bot token is not required for this option.
2. From the project root, start the local web server:

   ```powershell
   python UI/server.py
   ```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
4. Use the page to search a category, select an article to generate its post and caption, and adjust the post settings.

The web server binds to your own computer (`127.0.0.1`), so the interface is intended for local use. Keep the terminal open while using it; press Ctrl+C there to stop the server.

## Use the hosted Telegram bot

You can also use the hosted bot in Telegram without downloading or installing this project. Open **[t.me/NWFatherBot]** and press **Start**.

## Notes

- Generated images and descriptions are written under `output/` while the app is running. The SQLite databases are stored under `database/`.
- News availability depends on the configured API providers, their quotas, and the selected category.
- The browser interface loads styling and fonts from external CDNs, so those visual assets require an internet connection.
- The project includes an example API configuration only. Configure your own keys in `.env` before running it.
