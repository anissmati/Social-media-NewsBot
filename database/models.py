from dataclasses import dataclass

@dataclass
class User:
    telegram_id: int
    text_color: str
    gradient_color: str
    platform: str
    tone: str
    language: str
    credit: int
