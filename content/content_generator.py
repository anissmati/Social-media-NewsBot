import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_title(article, settings):
    tone = settings["tone"]
    lang = settings["language"]
    platform = settings["platform"]

    response = client.models.generate_content(
    model= "gemini-3.5-flash-lite",
    contents= f"title: {article['title']}, summary: {article['summary']}. "
        f"Using the title and the summary, generate a short, attractive, and easy-to-read title for a {platform} post. "
        f"The title must be written in {lang} and match a {tone} tone. "
        f"Keep it concise (max 8-10 words), catchy, and clear for a general audience. "
        f"Return just the new title with no other text, and without emojies"
    )
    return response.text

def generate_summary(article, settings):
    tone = settings["tone"]
    lang = settings["language"]
    platform = settings["platform"]
    
    response = client.models.generate_content(
    model= "gemini-3.5-flash-lite",
    contents= f"title: {article['title']}, summary: {article['summary']}. "
        f"Using the title and the summary, generate an engaging {platform} post description that tells the story of the article and details its core points. "
        f"Write it in {lang}, with a {tone} tone. "
        f"Make it easy to read for a general audience, and include relevant hashtags at the end. "
        f"Return just the final description text with no other conversational filler or emojis."
    )
    return response.text

