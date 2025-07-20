# tests/test_dynamic.py

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapers.dynamic_scraper import scrape_dynamic, DynamicScraper, run_dynamic_scraper

DYNAMIC_URL = "https://books.toscrape.com/catalogue/page-1.html"

class TestDynamicScraper:
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_dynamic_scraper_returns_data(self):
        """Test that dynamic scraper returns valid data"""
        data = await scrape_dynamic(DYNAMIC_URL, max_products=5)
        
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
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_dynamic_scraper_max_products_limit(self):
        """Test that scraper respects max_products limit"""
        max_products = 3
        data = await scrape_dynamic(DYNAMIC_URL, max_products=max_products)
        
        assert len(data) <= max_products, f"Should not exceed {max_products} products"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_dynamic_scraper_pagination(self):
        """Test that scraper can handle multiple pages"""
        data = await scrape_dynamic(DYNAMIC_URL, max_products=25)  # Should require pagination
        
        assert len(data) > 15, "Should scrape multiple pages"
        
        # Check that we have products from different pages
        names = [product["name"] for product in data]
        unique_names = set(names)
        assert len(unique_names) == len(names), "All products should be unique"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_dynamic_scraper_class_initialization(self):
        """Test DynamicScraper class initialization"""
        scraper = DynamicScraper()
        assert scraper.retry_count == 3
        assert scraper.base_url == "https://books.toscrape.com"
    
    @pytest.mark.asyncio
    async def test_dynamic_scraper_empty_url(self):
        """Test scraper behavior with invalid URL"""
        # This should fail gracefully and return empty list
        try:
            data = await scrape_dynamic("", max_products=5)
            assert isinstance(data, list), "Should return list even on error"
        except Exception:
            # It's acceptable for it to raise an exception with invalid URL
            pass
    
    def test_run_dynamic_scraper_function(self):
        """Test the run_dynamic_scraper convenience function"""
        # This test may create files, so we'll mock the file writing
        with patch('builtins.open'), patch('json.dump'), patch('os.makedirs'):
            data = run_dynamic_scraper()
            assert isinstance(data, list)

class TestDynamicScraperMocked:
    """Tests using mocked playwright components"""
    
    @pytest.mark.asyncio
    async def test_extract_single_product_success(self):
        """Test product extraction from a single element"""
        scraper = DynamicScraper()
        
        # Mock element
        mock_element = AsyncMock()
        
        # Mock sub-elements
        mock_name = AsyncMock()
        mock_name.get_attribute = AsyncMock(return_value="Test Book Title")
        
        mock_price = AsyncMock()
        mock_price.inner_text = AsyncMock(return_value="£12.99")
        
        mock_link = AsyncMock()
        mock_link.get_attribute = AsyncMock(return_value="test-book.html")
        
        mock_rating = AsyncMock()
        mock_rating.get_attribute = AsyncMock(return_value="star-rating Four")
        
        mock_availability = AsyncMock()
        mock_availability.inner_text = AsyncMock(return_value="In stock (22 available)")
        
        # Configure element to return mocked sub-elements
        async def mock_query_selector(selector):
            if "h3 a" in selector:
                return mock_name if "title" not in selector else mock_link
            elif "price_color" in selector:
                return mock_price
            elif "star-rating" in selector:
                return mock_rating
            elif "availability" in selector:
                return mock_availability
            return None
        
        mock_element.query_selector = mock_query_selector
        
        # Test extraction
        product = await scraper._extract_single_product(mock_element)
        
        assert product is not None
        assert product["name"] == "Test Book Title"
        assert product["price"] == "£12.99"
        assert "test-book.html" in product["link"]
        assert product["rating"] == "Four"
        assert "In stock" in product["availability"]
    
    @pytest.mark.asyncio
    async def test_extract_single_product_missing_data(self):
        """Test product extraction when some data is missing"""
        scraper = DynamicScraper()
        
        # Mock element with missing price
        mock_element = AsyncMock()
        
        async def mock_query_selector(selector):
            if "h3 a" in selector:
                mock_name = AsyncMock()
                mock_name.get_attribute = AsyncMock(return_value="Test Book")
                return mock_name
            elif "price_color" in selector:
                return None  # Missing price
            return None
        
        mock_element.query_selector = mock_query_selector
        
        # Should return None if essential data is missing
        product = await scraper._extract_single_product(mock_element)
        assert product is None
    
    @pytest.mark.asyncio
    async def test_navigate_to_next_page_success(self):
        """Test successful navigation to next page"""
        scraper = DynamicScraper()
        
        # Mock page
        mock_page = AsyncMock()
        
        # Mock next button
        mock_next_button = AsyncMock()
        mock_next_button.is_visible = AsyncMock(return_value=True)
        mock_next_button.is_enabled = AsyncMock(return_value=True)
        mock_next_button.click = AsyncMock()
        
        mock_page.query_selector = AsyncMock(return_value=mock_next_button)
        mock_page.expect_navigation = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        
        # Mock context manager for expect_navigation
        class MockNavigation:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
        
        mock_page.expect_navigation.return_value = MockNavigation()
        
        result = await scraper._navigate_to_next_page(mock_page)
        
        assert result is True
        mock_next_button.click.assert_called_once()
        mock_page.wait_for_load_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_navigate_to_next_page_no_button(self):
        """Test navigation when no next button exists"""
        scraper = DynamicScraper()
        
        # Mock page with no next button
        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        
        result = await scraper._navigate_to_next_page(mock_page)
        
        assert result is False

class TestAsyncUtils:
    
    @pytest.mark.asyncio
    async def test_async_backoff(self):
        """Test async backoff function"""
        import time
        from src.scrapers.dynamic_scraper import DynamicScraper
        
        scraper = DynamicScraper()
        
        start_time = time.time()
        await scraper._async_backoff()
        elapsed = time.time() - start_time
        
        assert elapsed >= 1.0, "Should wait at least 1 second"
        assert elapsed <= 4.0, "Should not wait more than 4 seconds normally"

# Integration tests
class TestDynamicIntegration:
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(150)
    async def test_end_to_end_dynamic_scraping(self):
        """End-to-end test of dynamic scraping process"""
        data = await scrape_dynamic(DYNAMIC_URL, max_products=8)
        
        assert len(data) > 0, "Should scrape some products"
        assert len(data) <= 8, "Should respect max products limit"
        
        # Validate all products have required data
        for product in data:
            assert product["name"], "Each product should have a name"
            assert product["price"], "Each product should have a price"
            assert product["link"], "Each product should have a link"
            
            # Additional fields should be present
            assert "rating" in product
            assert "availability" in product
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.timeout(200)
    async def test_large_dynamic_scraping_task(self):
        """Test scraping a larger number of products with dynamic scraper"""
        data = await scrape_dynamic(DYNAMIC_URL, max_products=25)
        
        assert len(data) >= 15, "Should scrape at least 15 products"
        assert len(data) <= 25, "Should respect max products limit"
        
        # Check data quality
        names = [p["name"] for p in data]
        assert len(set(names)) == len(names), "All product names should be unique"
        
        prices = [p["price"] for p in data]
        assert all(price for price in prices), "All products should have prices"
        
        links = [p["link"] for p in data]
        assert all(link and link.startswith("http") for link in links), "All links should be valid URLs"

# Performance tests
class TestPerformance:
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_dynamic_scraper_performance(self):
        """Test that dynamic scraper completes within reasonable time"""
        import time
        
        start_time = time.time()
        data = await scrape_dynamic(DYNAMIC_URL, max_products=10)
        elapsed = time.time() - start_time
        
        assert len(data) > 0, "Should return some data"
        assert elapsed < 120, "Should complete within 2 minutes for 10 products"
        
        # Calculate products per second
        rate = len(data) / elapsed if elapsed > 0 else 0
        assert rate > 0.05, "Should scrape at least 1 product per 20 seconds"