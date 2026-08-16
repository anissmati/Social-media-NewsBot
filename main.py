import sys
sys.modules['nltk.inisec'] = type('mock', (object,), {'find_spec': lambda *args, **kwargs: None})

from Searcher.main import run_pipeline_1
from content.main import run_pipeline_2


if __name__ == "__main__":
    print("Run the Telegram bot with telegram/main.py.")
