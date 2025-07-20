import asyncio
import json
import logging
from typing import List, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from src.config import Config

class DynamicScraper:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def scrape_dynamic(self, url: str, max_products: int = 50) -> List[Dict]:
        products = []

        self.logger.info(f"Launching browser for URL: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                self.logger.info(f"Navigating to {url} with timeout 20s")
                await page.goto(url, timeout=20000)
                self.logger.debug("Waiting for __NEXT_DATA__ script tag")
                script = await page.wait_for_selector('script#__NEXT_DATA__', timeout=20000)
                content = await script.inner_text()
                self.logger.debug("Extracted __NEXT_DATA__ content")

                data = json.loads(content)

                product_list = data.get("props", {}).get("pageProps", {}).get("product_list", [])
                self.logger.info(f"Found {len(product_list)} products in JSON data")

                for p_item in product_list[:max_products]:
                    product = {
                        "id": p_item.get("id"),
                        "name": p_item.get("name"),
                        "slug": p_item.get("slug"),
                        "price": p_item.get("price"),
                        "regular_price": p_item.get("regular_price"),
                        "image": p_item.get("featured_image"),
                        "description": p_item.get("description"),
                        "url": f"https://electricbikecompany.com/shop/products/{p_item.get('slug')}"
                    }
                    products.append(product)

            except PlaywrightTimeoutError as e:
                self.logger.error(f"Timeout while waiting for page or elements: {e}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON from __NEXT_DATA__: {e}")
            except Exception as e:
                self.logger.error(f"Error during scraping: {e}")
            finally:
                await browser.close()
                self.logger.info("Browser closed, scraping finished")

        return products

async def scrape_dynamic(url: str, max_products: int = 50, config: Config = Config()) -> List[Dict]:
    scraper = DynamicScraper(config)
    return await scraper.scrape_dynamic(url, max_products)
