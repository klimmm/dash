import os
import re
import json
import time
import random
import logging
from typing import List, Tuple, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import scraper_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class Scraper:
    def __init__(self):
        self.driver = self.setup_driver()
        self.session = self.create_session()

    def check_internet_connection(self) -> bool:
        """Check if there's an active internet connection."""
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def setup_driver(self) -> webdriver.Chrome:
        """Set up and return a configured Chrome WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": scraper_config.DOWNLOAD_FOLDER,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        try:
            if self.check_internet_connection():
                logger.info("Internet connection available. Attempting to download latest ChromeDriver.")
                chromedriver_path = ChromeDriverManager().install()
            else:
                logger.warning("No internet connection. Falling back to local ChromeDriver.")
                chromedriver_path = self.get_local_chromedriver()

            logger.info(f"ChromeDriver path: {chromedriver_path}")

            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(f"ChromeDriver not found at {chromedriver_path}")

            if not os.access(chromedriver_path, os.X_OK):
                logger.warning(f"ChromeDriver at {chromedriver_path} is not executable. Attempting to set permissions.")
                os.chmod(chromedriver_path, 0o755)

            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("ChromeDriver setup successful.")
            return driver
        except Exception as e:
            logger.error(f"Error setting up ChromeDriver: {str(e)}", exc_info=True)
            raise

    def get_local_chromedriver(self) -> str:
        """Return the path to a locally stored ChromeDriver."""
        local_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
        if os.path.exists(local_path):
            return local_path
        else:
            raise FileNotFoundError("Local ChromeDriver not found. Please download a compatible ChromeDriver and place it in the script directory.")


    def create_session(self) -> requests.Session:
        """Create and return a configured requests Session."""
        session = requests.Session()
        retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        return session

    def manual_intervention(self, url: str) -> List[Dict[str, str]]:
        """Handle manual intervention for DDOS-GUARD challenges."""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("detach", True)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(url)
        logger.info("Please complete the DDOS-GUARD challenge manually.")
        logger.info("After you've successfully accessed the page, press Enter in this console.")
        input()

        cookies = driver.get_cookies()
        driver.quit()

        return cookies

    def get_excel_links(self, page_url: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
        """Extract Excel file links from the given page URL."""
        try:
            logger.info(f"Attempting to access {page_url}")
            self.driver.get(page_url)

            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")

            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )

            links = self.driver.find_elements(By.TAG_NAME, "a")
            logger.info(f"Total links found: {len(links)}")

            excel_links = []
            for link in links:
                href = link.get_attribute("href")
                text = link.text
                if href and (href.endswith('.xlsx') or href.endswith('.xls') or 'excel' in href.lower()):
                    file_url = href
                    file_name = text.strip() if text else "Unnamed Excel File"
                    excel_links.append((file_url, file_name))
                    logger.info(f"Excel link found: {file_url}")

            if not excel_links:
                logger.warning(f"No Excel links found on {page_url}")
                logger.info("Page source preview:")
                logger.info(self.driver.page_source[:1000])
            else:
                logger.info(f"Total Excel links found: {len(excel_links)}")

            return excel_links, None
        except Exception as e:
            logger.error(f"Failed to access {page_url}: {str(e)}", exc_info=True)
            return [], f"Failed to access {page_url}: {str(e)}"

    def download_excel_file(self, url: str, filename: str, max_retries: int = 3, timeout: int = 30) -> str:
        """Download an Excel file from the given URL."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to download: {filename} (Attempt {attempt + 1}/{max_retries})")

                cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
                response = self.session.get(url, cookies=cookies, timeout=timeout)
                response.raise_for_status()

                file_path = os.path.join(scraper_config.DOWNLOAD_FOLDER, filename)
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                logger.info(f"Successfully downloaded: {filename}")
                return f"Downloaded {filename}"

            except requests.RequestException as e:
                logger.error(f"Error downloading {filename}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return f"Failed to download {filename} after {max_retries} attempts"

            except Exception as e:
                logger.error(f"Unexpected error while downloading {filename}: {str(e)}")
                return f"Failed to download {filename}: Unexpected error - {str(e)}"

    def process_page(self, page_url: str, name_mapping: Dict[str, str]) -> None:
        """Process a single page, extracting and downloading Excel files."""
        try:
            year_q = re.search(r'(\d{4}_\d)', page_url).group(1)
        except AttributeError:
            logger.error(f"Error: Unable to extract year and quarter from URL: {page_url}")
            return

        excel_links, error = self.get_excel_links(page_url)

        if error:
            logger.error(error)
            return

        if not excel_links:
            logger.warning(f"No Excel links found on {page_url}")
            return

        for i, (file_url, file_name) in enumerate(excel_links, start=1):
            short_name = self.assign_short_name(file_name, name_mapping)
            if short_name in scraper_config.SELECTED_FILES:
                filename = f"{short_name}_{year_q}.xlsx"
                result = self.download_excel_file(file_url, filename)
                logger.info(result)
                time.sleep(random.uniform(3, 7))

    @staticmethod
    def assign_short_name(original_name: str, name_mapping: Dict[str, str]) -> str:
        """
        Assign a short name based on the original filename and mapping.
        Uses exact matching first, then falls back to substring matching with length prioritization.
        
        Args:
            original_name: The original filename to match
            name_mapping: Dictionary mapping original names to short names
        
        Returns:
            str: The mapped short name or 'misc' if no match found
        """
        # Normalize the original name
        original_name_lower = original_name.lower().strip()
        
        # Try exact match first
        for key in name_mapping:
            if key.lower().strip() == original_name_lower:
                return name_mapping[key]
        
        # Group mappings by their short names to handle conflicts
        reverse_mapping = {}
        for key, value in name_mapping.items():
            if value not in reverse_mapping:
                reverse_mapping[value] = []
            reverse_mapping[value].append(key.lower())
        
        # For each group of keys that map to the same short name
        matches = []
        for key in name_mapping:
            key_lower = key.lower()
            if key_lower in original_name_lower:
                matches.append((key, len(key)))
        
        # Sort matches by length (longest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # If we have matches, return the mapping for the longest matching key
        if matches:
            return name_mapping[matches[0][0]]
        
        return 'misc'

    @staticmethod
    def load_json(file_path: str) -> Dict:
        """Load and return JSON data from a file."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def run(self):
        """Run the scraping process."""
        name_mapping = self.load_json(scraper_config.NAME_MAPPING_FILE)
        base_urls = self.load_json(scraper_config.BASE_URLS_FILE)

        os.makedirs(scraper_config.DOWNLOAD_FOLDER, exist_ok=True)

        cookies = self.manual_intervention(base_urls[0])

        try:
            for url in base_urls:
                logger.info(f"Processing {url}")

                self.driver.get("https://www.cbr.ru")
                for cookie in cookies:
                    self.driver.add_cookie(cookie)

                self.driver.get(url)
                time.sleep(5)

                if "DDOS-GUARD" in self.driver.title:
                    logger.error(f"DDOS-GUARD present for {url}. Manual intervention may be needed.")
                    cookies = self.manual_intervention(url)
                    continue

                self.process_page(url, name_mapping)

                logger.info("Finished processing URL")
                time.sleep(random.uniform(5, 10))
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        finally:
            self.driver.quit()

if __name__ == "__main__":
    try:
        scraper = Scraper()
        scraper.run()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)