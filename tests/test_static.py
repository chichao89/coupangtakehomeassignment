# tests/test_static.py

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapers.static_scraper import scrape_static, StaticScraper
from src.utils.anti_bot import get_headers, rotate_proxy
from src.utils.pagination import get_next_page

STATIC_URL = "https://books.toscrape.com/catalogue/page-1.html"

class TestStaticScraper:
    
    @pytest.mark.timeout(60)
    def test_static_scraper_returns_data(self):
        """Test that static scraper returns valid data"""
        data = scrape_static(STATIC_URL, max_products=5)
        
        assert isinstance(data, list), "Expected result to be a list"
        assert len(data) > 0, "Expected at least one product"
        
        # Validate product structure
        product = data[0]
        required_fields = ["name", "price", "link"]
        
        for field in required_fields:
            assert field in product, f"Missing '{field}' field"
            assert product[field] is not None, f"Field '{field}' should not be None"
        
        # Validate data types and content
        assert isinstance(product["name"], str), "Product name should be a string"
        assert isinstance(product["price"], str), "Product price should be a string"
        assert isinstance(product["link"], str), "Product link should be a string"
        
        # Price should contain currency symbol
        assert any(symbol in product["price"] for symbol in ["£", "$", "€"]), "Price should contain currency"
        
        # Link should be a valid URL
        assert product["link"].startswith("http"), "Link should be a valid URL"
    
    @pytest.mark.timeout(30)
    def test_static_scraper_max_products_limit(self):
        """Test that scraper respects max_products limit"""
        max_products = 3
        data = scrape_static(STATIC_URL, max_products=max_products)
        
        assert len(data) <= max_products, f"Should not exceed {max_products} products"
    
    @pytest.mark.timeout(90)
    def test_static_scraper_pagination(self):
        """Test that scraper can handle multiple pages"""
        data = scrape_static(STATIC_URL, max_products=25)  # Should require pagination
        
        assert len(data) > 20, "Should scrape multiple pages"
        
        # Check that we have products from different pages (prices should vary)
        prices = [product["price"] for product in data]
        unique_prices = set(prices)
        assert len(unique_prices) > 5, "Should have variety from multiple pages"
    
    def test_static_scraper_empty_url(self):
        """Test scraper behavior with invalid URL"""
        data = scrape_static("", max_products=5)
        assert isinstance(data, list), "Should return empty list for invalid URL"
    
    def test_static_scraper_class_initialization(self):
        """Test StaticScraper class can be initialized"""
        scraper = StaticScraper()
        assert scraper.retry_count == 3
        assert scraper.base_url == "https://books.toscrape.com"
    
    @patch('src.scrapers.static_scraper.requests.Session.get')
    def test_static_scraper_error_handling(self, mock_get):
        """Test error handling in static scraper"""
        # Mock a failed request
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server Error")
        mock_get.return_value = mock_response
        
        scraper = StaticScraper()
        data = scraper.scrape_static(STATIC_URL, max_products=5)
        
        # Should return empty list on error
        assert isinstance(data, list)
    
    @patch('src.scrapers.static_scraper.requests.Session.get')
    def test_static_scraper_rate_limit_handling(self, mock_get):
        """Test rate limit (429) handling"""
        # Mock a rate limit response then success
        mock_429_response = Mock()
        mock_429_response.status_code = 429
        
        mock_200_response = Mock()
        mock_200_response.status_code = 200
        mock_200_response.text = '''
        <html>
            <article class="product_pod">
                <h3><a title="Test Book" href="test.html"></a></h3>
                <p class="price_color">£10.00</p>
                <p class="star-rating Three"></p>
                <p class="instock availability">In stock</p>
            </article>
        </html>
        '''
        
        mock_get.side_effect = [mock_429_response, mock_200_response]
        
        scraper = StaticScraper()
        data = scraper.scrape_static(STATIC_URL, max_products=1)
        
        # Should handle rate limit and return data on retry
        assert len(mock_get.call_args_list) == 2  # Called twice
        assert isinstance(data, list)

class TestAntiBot:
    
    def test_get_headers(self):
        """Test header generation"""
        headers = get_headers()
        
        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        
        # Should vary between calls
        headers2 = get_headers()
        # User-Agent might be different (random selection)
        assert isinstance(headers2, dict)
    
    def test_rotate_proxy(self):
        """Test proxy rotation"""
        proxy = rotate_proxy()
        assert isinstance(proxy, dict)
    
    def test_backoff_function(self):
        """Test backoff timing"""
        import time
        
        start_time = time.time()
        from src.utils.anti_bot import backoff
        backoff()  # Normal backoff
        elapsed = time.time() - start_time
        
        assert elapsed >= 1.0, "Should wait at least 1 second"
        assert elapsed <= 4.0, "Should not wait more than 4 seconds normally"

class TestPagination:
    
    def test_get_next_page_function(self):
        """Test get_next_page function"""
        from bs4 import BeautifulSoup
        
        # Mock HTML with next button
        html = '''
        <html>
            <li class="next">
                <a href="page-2.html">next</a>
            </li>
        </html>
        '''
        
        soup = BeautifulSoup(html, "html.parser")
        next_url = get_next_page(soup)
        
        assert next_url is not None
        assert "page-2.html" in next_url
    
    def test_get_next_page_no_next(self):
        """Test get_next_page when no next button exists"""
        from bs4 import BeautifulSoup
        
        html = '<html><div>No pagination</div></html>'
        soup = BeautifulSoup(html, "html.parser")
        next_url = get_next_page(soup)
        
        assert next_url is None

# Integration tests
class TestIntegration:
    
    @pytest.mark.timeout(120)
    def test_end_to_end_static_scraping(self):
        """End-to-end test of static scraping process"""
        data = scrape_static(STATIC_URL, max_products=10)
        
        assert len(data) > 0, "Should scrape some products"
        assert len(data) <= 10, "Should respect max products limit"
        
        # Validate all products have required data
        for product in data:
            assert product["name"], "Each product should have a name"
            assert product["price"], "Each product should have a price"
            assert product["link"], "Each product should have a link"
            
            # Additional fields should be present
            assert "rating" in product
            assert "availability" in product
    
    @pytest.mark.slow
    @pytest.mark.timeout(180)  
    def test_large_scraping_task(self):
        """Test scraping a larger number of products (closer to assignment requirement)"""
        data = scrape_static(STATIC_URL, max_products=30)
        
        assert len(data) >= 20, "Should scrape at least 20 products"
        assert len(data) <= 30, "Should respect max products limit"
        
        # Check data quality
        names = [p["name"] for p in data]
        assert len(set(names)) == len(names), "All product names should be unique"
        
        prices = [p["price"] for p in data]
        assert all(price for price in prices), "All products should have prices"