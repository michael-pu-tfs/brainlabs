import pandas as pd
import time
import logging
import json
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse

# Setup logger
os.makedirs("logs", exist_ok=True)
os.makedirs("scraped_json", exist_ok=True)

logging.basicConfig(
    filename="logs/scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Add StreamHandler to show logs in the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(console_handler)


class PageScraper:
    def __init__(self, soup, title=""):
        self.soup = soup
        self.title = title

    def get_url_slug(self, url):
        parsed_url = urlparse(url)
        # Extracting the path after the base URL and removing leading/trailing slashes
        return parsed_url.path.strip("/")

    def get_description(self):
        desc_tag = self.soup.find("meta", attrs={"name": "description"})
        return desc_tag.get("content", "") if desc_tag else ""

    def get_headings(self):
        h1 = self.soup.find_all("h1")
        h2 = self.soup.find_all("h2")
        h3 = self.soup.find_all("h3")
        return {
            "h1": [h.text.strip() for h in h1] if h1 else [],
            "h2": [h.text.strip() for h in h2] if h2 else [],
            "h3": [h.text.strip() for h in h3] if h3 else [],
        }

    def get_on_page_copy(self):
        """
        Extract meaningful text from web page while skipping headers, footers,
        and other non-content elements.
        """
        for button in self.soup.find_all(attrs={"role": "button"}):
            button.decompose()

        # Remove unnecessary elements
        for hidden in self.soup(
            [
                "script",
                "style",
                "meta",
                "noscript",
                "svg",
                "iframe",
                "form",
                "button",
                "link",
            ]
        ):
            hidden.decompose()

        with open("scraped_html.txt", "w") as f:
            f.write(str(self.soup))
        # Remove elements typically in headers and footers
        header_footer_selectors = [
            ".header",
            ".footer",
            "#header",
            "#footer",
            "header",
            "footer",
            ".site-header",
            ".site-footer",
            ".main-header",
            ".main-footer",
            "nav",
            ".navigation",
            "#navigation",
            ".pdp-header",
        ]

        for selector in header_footer_selectors:
            for element in self.soup.select(selector):
                element.decompose()

        # List of content-rich elements to extract
        content_elements = [
            "h1",
            "h2",
            "h3",
            "h4",
            "div",
            "p",
            "ul",
            "ol",
            "span",
            "article",
            "section",
        ]

        # Data collection with improved filtering
        data = [{"title": self.title}]

        for element_type in content_elements:
            sub_data = {element_type: []}
            all_tags = self.soup.find_all(element_type)

            for tag in all_tags:
                # Additional filtering to remove short or irrelevant text
                text = tag.get_text(" ", strip=True)

                # Skip very short text (likely not meaningful content)
                if len(text) < 10:
                    continue

                # Skip text with too many numbers or special characters
                if self._is_noise(text):
                    continue

                # Avoid duplicates
                if text and text not in sub_data[element_type]:
                    sub_data[element_type].append(text)

            # Only add non-empty element types
            if sub_data[element_type]:
                data.append(sub_data)

        return data

    def _is_noise(self, text, max_noise_ratio=0.4):
        if not text:
            return True

        # Count alphabetic and non-alphabetic characters
        alphabetic_count = sum(1 for char in text if char.isalpha())
        total_count = len(text)

        # Calculate noise ratio
        noise_ratio = 1 - (alphabetic_count / total_count)

        return noise_ratio > max_noise_ratio

    def scrape_page(self):
        return {
            "title": self.soup.title.string.strip() if self.soup.title else "",
            "meta_desc": self.get_description(),
            "h1": self.get_headings()["h1"],
            "h2": self.get_headings()["h2"],
            "h3": self.get_headings()["h3"],
            "page_text": self.get_on_page_copy(),
        }


async def scrape_data(url: str) -> dict:
    logging.info(f"Starting to scrape URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

        page = await browser.new_page(user_agent=ua)
        try:
            await page.goto(url, timeout=100000)
            logging.info(f"Successfully accessed URL: {url}")
        except PlaywrightTimeoutError as e:
            logging.error(f"Timeout error while accessing URL {url}: {e}")
            return {"origin_url": url, "error": "Timeout error"}
        await page.wait_for_load_state("load")
        time.sleep(4)
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        os.makedirs("scraped_html", exist_ok=True)
        filename = f"scraped_html/{url.replace('https://', '').replace('/', '_')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"HTML content saved to {filename}")

        title = await page.title()
        page_url = page.url
        scraper = PageScraper(soup, title)
        headings = scraper.get_headings()
        page_text = scraper.get_on_page_copy()
        await browser.close()

        logging.info(f"Successfully scraped data from URL: {url}")
        result_df = {
            "title": title,
            "meta_desc": scraper.get_description(),
            "h1": headings["h1"] if headings["h1"] else "",
            "h2": headings["h2"] if len(headings["h2"]) > 0 else "",
            "h3": headings["h3"] if len(headings["h3"]) > 1 else "",
            "page_text": page_text,
        }

        print(result_df)
        # Create JSON object
        scraped_data = {
            "origin_url": url,
            "title": title,
            "meta_desc": scraper.get_description(),
            "h1-1": headings["h1"][0] if headings["h1"] else "",
            "H2-1": headings["h2"][0] if len(headings["h2"]) > 0 else "",
            "H2-2": headings["h2"][1] if len(headings["h2"]) > 1 else "",
            "url_slug": scraper.get_url_slug(url),
            "page_text": result_df,  # Use the dictionary directly
        }

        # Save individual JSON file for each URL
        json_file_path = os.path.join("scraped_json", f"{page_url.split('/')[-1]}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(result_df, f, ensure_ascii=False, indent=4)

        logging.info(f"Saved scraped data to JSON: {json_file_path}")

        return scraped_data


async def scrape_url(url: str) -> pd.DataFrame:
    logging.info(f"Starting scraping for URL: {url}")
    result = await scrape_data(url)
    logging.info("Scraping completed.")
    return pd.DataFrame([result])
