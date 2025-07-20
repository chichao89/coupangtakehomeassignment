#src/config.py
from typing import List

class Config:
    TARGET_URLS: List[str] = [
        "https://books.toscrape.com/",              # Static HTML
        "https://quotes.toscrape.com/js/",          # Dynamic (Playwright)
    ]

    MAX_PRODUCTS: int = 50
    REQUEST_TIMEOUT: int = 10
    REQUEST_DELAY: float = 1.5

    ROTATE_USER_AGENTS: bool = True

    LOG_LEVEL: str = "INFO"
