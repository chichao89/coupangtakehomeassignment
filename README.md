# 🛒 E-Commerce Web Scraper

A modular Python-based web scraper for extracting product information from e-commerce websites. Supports both static HTML pages and dynamic JavaScript-rendered content.

![Project Structure](https://img.shields.io/badge/status-active-success.svg) 
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)


## 📋 Table of Contents

- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output](#-output)
- [Testing](#-testing)
- [Design Highlights](#-design-highlights)
- [Known Limitations](#️-known-limitations)
- [Author Notes](#-author-notes)

## 📁 Project Structure

```
coupangtakehomeassignment/
├── src/
│   ├── scrapers/
│   │   ├── static_scraper.py       # Scraper for static HTML pages
│   │   └── dynamic_scraper.py      # Scraper for dynamic JS-rendered content
│   └── utils/
│       ├── anti_bot.py             # User-agent rotation, retry/backoff utilities
│       └── pagination.py           # Handles pagination logic across pages
├── tests/
│   ├── test_static.py              # Unit tests for static scraper
│   └── test_dynamic.py             # Unit tests for dynamic scraper
├── data/
│   └── output.json                 # Sample output data file
├── requirements.txt                # Project dependencies
├── README.md                       # Documentation file
└── run.py                         # Main CLI entrypoint
```

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chichao89/coupangtakehomeassignment.git
   cd coupangtakehomeassignment
   ```

2. **Install dependencies:** -- for mac
   ```bash
   python3 -m venv venv
   source venv/bin/activate 
   pip install -r requirements.txt
   playwright install
   ```

## 💻 Usage

### Basic Commands

**For static scraping:**
```bash
python run.py --mode static --url "https://example.com" --max-products 50 --output-format csv
python run.py --mode static --url "https://books.toscrape.com/" --output-format both
python3 run.py --mode static --url "https://books.toscrape.com/" --max-products 50 --output-format both
python3 run.py --mode static --url "https://books.toscrape.com/" --max-products 0 --output-format both  
```
For full scraping products use --max-products 0

**For dynamic scraping (JavaScript-heavy sites):**
```bash
python run.py --mode dynamic --url "https://example.com" --max-products 30 --output-format json
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Scraping mode (static or dynamic) | static |
| `--url` | Target URL to scrape | Required |
| `--max-products` | Maximum number of products to scrape | 0 | for maximum
| `--output-format` | Output format (json or csv) | json |
| `--headless` | Run browser in headless mode (dynamic) | True |

### Example Command

```bash
python run.py --mode dynamic --url "https://electricbikecompany.com/shop" --max-products 25 --output-format csv
```

## 📊 Output

Data files are saved in the `data/` directory with timestamps:

```
data/
├── products_20250720_1105.csv
└── products_20250720_1123.json
```

## 🧪 Testing

Run unit tests with pytest:

```bash
pytest tests/
```

## ✨ Design Highlights

- **Modular Architecture:** Clear separation of static and dynamic scraping logic
- **Smart Pagination:** Custom pagination handling for different website structures
- **JavaScript Support:** Playwright integration for JavaScript-heavy pages
- **Robust Error Handling:** Comprehensive logging and error handling throughout
- **Anti-Detection:** Anti-bot features to reduce detection risk

## ⚠️ Known Limitations

- ❌ No support for infinite scroll or API sniffing
- ❌ Lacks CAPTCHA solving and proxy rotation  
- ❌ Dynamic scraping may face timeouts on protected sites
- ❌ Dynamic scraping will not work on current code
- ❌ Util methods have not been tested 

*These are potential areas for future improvement.*

## 👨‍💻 Author Notes

> "This project offers a practical foundation for e-commerce web scraping. While dynamic scraping via Playwright can face challenges on sites with advanced bot protection, the modular design allows easy future extension with stealth plugins, proxies, or login simulation."
