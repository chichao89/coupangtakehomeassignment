#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from src.scrapers.static_scraper import StaticScraper
from src.scrapers.dynamic_scraper import scrape_dynamic
from src.config import Config
import json
import csv

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_csv(data, path):
    if not data:
        return
    keys = data[0].keys()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(data)

def setup_logger(level: str):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger()

def main():
    parser = argparse.ArgumentParser(description="Simple Web Scraper Runner")
    parser.add_argument("--mode", choices=["static", "dynamic", "both"], default="static")
    parser.add_argument("--url", help="Target URL to scrape")
    parser.add_argument("--max-products", type=int, default=50)
    parser.add_argument("--output-format", choices=["json", "csv", "both"], default="json")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    config = Config()
    if args.max_products is not None:
        config.MAX_PRODUCTS = args.max_products
    log_level = "DEBUG" if args.verbose else config.LOG_LEVEL

    logger = setup_logger(log_level)
    target_url = args.url or config.TARGET_URLS[0]

    all_products = []

    try:
        if args.mode == "static":
            logger.info(f"Starting static scraper for {target_url}")
            scraper = StaticScraper(config=config, logger=logger)
            products = scraper.scrape_static(target_url, config.MAX_PRODUCTS)
            all_products.extend(products)

        elif args.mode == "dynamic":
            logger.info(f"Starting dynamic scraper for {target_url}")
            products = asyncio.run(scrape_dynamic(target_url, config.MAX_PRODUCTS, config))
            all_products.extend(products)

        elif args.mode == "both":
            logger.info(f"Starting static scraper for {target_url}")
            static_scraper = StaticScraper(config=config, logger=logger)
            static_products = static_scraper.scrape_static(target_url, config.MAX_PRODUCTS // 2)
            logger.info(f"Starting dynamic scraper for {target_url}")
            dynamic_products = asyncio.run(scrape_dynamic(target_url, config.MAX_PRODUCTS // 2, config))
            all_products.extend(static_products)
            all_products.extend(dynamic_products)

        logger.info(f"Scraping completed. Extracted {len(all_products)} products")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        saved_files = []

        if args.output_format in ["json", "both"]:
            json_path = output_dir / f"products_{timestamp}.json"
            save_json(all_products, json_path)
            saved_files.append(str(json_path))

        if args.output_format in ["csv", "both"]:
            csv_path = output_dir / f"products_{timestamp}.csv"
            save_csv(all_products, csv_path)
            saved_files.append(str(csv_path))

        logger.info(f"Saved output files: {', '.join(saved_files)}")
        print(f"Scraping done. Extracted {len(all_products)} products.")
        print(f"Output files: {', '.join(saved_files)}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
