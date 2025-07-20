from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class PaginationHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.visited_urls = set()

    def get_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        next_url = self._find_next_button(soup)
        if next_url:
            full_url = urljoin(current_url, next_url)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                return full_url

        next_url = self._find_numbered_next(soup, current_url)
        if next_url:
            full_url = urljoin(current_url, next_url)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                return full_url

        next_url = self._find_load_more(soup)
        if next_url:
            full_url = urljoin(current_url, next_url)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                return full_url

        next_url = self._construct_next_page_url(current_url)
        if next_url:
            full_url = urljoin(current_url, next_url)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                return full_url

        return None

    def _find_next_button(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            "li.next a",
            ".next a",
            "a.next",
            ".pagination .next",
            ".pager-next a",
            ".next-page",
            "[rel='next']",
            "a[aria-label*='next']",
            "a[title*='next']",
            ".pagination-next a",
        ]
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    href = element.get('href')
                    if href:
                        return href
            except Exception as e:
                logger.debug(f"Error finding next button with selector {selector}: {e}")
                continue
        return None

    def _find_numbered_next(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        try:
            current_page = self._extract_page_number(current_url)
            pagination_selectors = [
                ".pagination", ".pager", ".page-numbers", ".paginate", ".page-nav", ".pagination-wrapper"
            ]
            for selector in pagination_selectors:
                pagination = soup.select_one(selector)
                if pagination:
                    page_links = pagination.find_all('a', href=True)
                    for link in page_links:
                        link_text = link.get_text(strip=True)
                        if link_text.isdigit():
                            page_num = int(link_text)
                            if current_page and page_num == current_page + 1:
                                return link['href']
                        elif link_text.lower() in ['next', '>', '→']:
                            return link['href']
        except Exception as e:
            logger.debug(f"Error in numbered pagination detection: {e}")
        return None

    def _find_load_more(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            ".load-more", ".show-more", ".view-more",
            "[data-next-url]", "[data-load-more]", ".infinite-scroll",
        ]
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    for attr in ['data-next-url', 'data-load-more', 'data-url', 'href']:
                        url = element.get(attr)
                        if url:
                            return url
            except Exception as e:
                logger.debug(f"Error with load more selector {selector}: {e}")
                continue
        return None

    def _construct_next_page_url(self, current_url: str) -> Optional[str]:
        try:
            parsed = urlparse(current_url)
            path_patterns = [
                (r'/page[-_/](\d+)', '/page-{}'),
                (r'/page[-_/](\d+)/', '/page-{}/'),
                (r'page[-_](\d+)\.html', 'page-{}.html'),
                (r'p(\d+)\.html', 'p{}.html'),
            ]

            for pattern, replacement in path_patterns:
                match = re.search(pattern, parsed.path)
                if match:
                    current_page = int(match.group(1))
                    next_page = current_page + 1
                    new_path = re.sub(pattern, replacement.format(next_page), parsed.path)
                    return parsed._replace(path=new_path).geturl()

            query_params = parse_qs(parsed.query)
            for param in ['page', 'p', 'pagenum', 'offset', 'start']:
                if param in query_params:
                    try:
                        current_page = int(query_params[param][0])
                        next_page = current_page + 1
                        query_params[param] = [str(next_page)]
                        new_query = '&'.join(f"{k}={v[0]}" for k, v in query_params.items())
                        return parsed._replace(query=new_query).geturl()
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            logger.debug(f"Error constructing next page URL: {e}")
        return None

    def _extract_page_number(self, url: str) -> Optional[int]:
        try:
            path_match = re.search(r'/page[-_/]?(\d+)', url)
            if path_match:
                return int(path_match.group(1))

            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            for param in ['page', 'p', 'pagenum']:
                if param in query_params:
                    try:
                        return int(query_params[param][0])
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass
        return None

    def get_all_page_urls(self, soup: BeautifulSoup, current_url: str, max_pages: int = 100) -> List[str]:
        page_urls = []
        try:
            selectors = [".pagination a", ".pager a", ".page-numbers a"]
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(current_url, href)
                        if full_url not in page_urls and len(page_urls) < max_pages:
                            page_urls.append(full_url)
        except Exception as e:
            logger.debug(f"Error getting all page URLs: {e}")
        return page_urls

# Custom logic for books.toscrape.com
def get_next_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    next_button = soup.select_one("li.next a")
    if next_button:
        href = next_button.get("href")
        if href:
            return urljoin(base_url, href)
    return None

def reset_pagination_handler():
    pass
