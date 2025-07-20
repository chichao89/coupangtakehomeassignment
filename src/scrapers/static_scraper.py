import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from src.config import Config
from urllib.parse import urljoin
import logging

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
]

class StaticScraper:
    def __init__(self, config: Config = Config(), logger: Optional[logging.Logger] = None):
        self.config = config
        self.base_url = "https://books.toscrape.com"
        self.session = requests.Session()
        self.logger = logger or logging.getLogger(__name__)

    def get_headers(self) -> Dict[str, str]:
        import random
        if self.config.ROTATE_USER_AGENTS:
            ua = random.choice(USER_AGENTS)
        else:
            ua = USER_AGENTS[0]
        return {"User-Agent": ua}

    def scrape_static(self, url: str, max_products: int = 50) -> List[Dict]:
        products = []
        current_url = url or self.base_url

        while current_url:
            self.logger.info(f"Scraping page: {current_url}")
            try:
                resp = self.session.get(current_url, headers=self.get_headers(), timeout=self.config.REQUEST_TIMEOUT)
                resp.raise_for_status()
            except Exception as e:
                self.logger.error(f"[StaticScraper] Request failed: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("article.product_pod")

            for item in items:
                if max_products and len(products) >= max_products:
                    break

                name = item.h3.a.get("title", "").strip()
                price_el = item.select_one("p.price_color")
                price = price_el.text.strip() if price_el else ""
                link = item.h3.a.get("href", "")
                if not link.startswith("http"):
                    link = urljoin(current_url, link)

                product = {"name": name, "price": price, "link": link}
                products.append(product)

            self.logger.info(f"Collected {len(products)} products so far")

            if max_products and len(products) >= max_products:
                break

            next_button = soup.select_one("li.next > a")
            if next_button:
                next_href = next_button.get("href")
                current_url = urljoin(current_url, next_href)
            else:
                current_url = None

            time.sleep(self.config.REQUEST_DELAY)

        self.logger.info(f"Scraping finished. Total products collected: {len(products)}")
        return products

def scrape_static(url: str, max_products: int = 50, config: Config = Config(), logger: Optional[logging.Logger] = None) -> List[Dict]:
    scraper = StaticScraper(config=config, logger=logger)
    return scraper.scrape_static(url, max_products)
