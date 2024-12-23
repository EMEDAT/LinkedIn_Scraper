import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from .utils import init_selenium_driver
import logging
import time
import random
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login_with_cookie(driver, cookie: str) -> bool:
    """
    Log in to LinkedIn using cookies with improved error handling.
    Returns True if login successful, False otherwise.
    """
    try:
        driver.get("https://www.linkedin.com/")
        driver.add_cookie({"name": "li_at", "value": cookie})
        driver.refresh()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "global-nav__primary-link"))
        )
        return True
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

def build_linkedin_url(query_params: Dict, filters: Dict = None) -> str:
    """
    Build LinkedIn search URL from query parameters and optional filters.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = [f"{key}={requests.utils.quote(str(value))}" for key, value in query_params.items() if value]
    if filters:
        params += [f"{key}={requests.utils.quote(str(value))}" for key, value in filters.items() if value]
    return base_url + "&".join(params)


def scrape_linkedin_profiles(query_params: Dict, cookie: str, filters: Dict = None) -> List[Dict]:
    """
    Scrape LinkedIn profiles using Selenium with improved error handling and rate limiting.
    Now supports an optional 'filers' argument.
    """
    # Incorporate 'filters' into the scraping logic if needed
    driver = init_selenium_driver()
    profiles = []
    page = 1
    max_pages = 3  # Adjust based on your needs
    try:
        if not login_with_cookie(driver, cookie):
            return profiles

        while page <= max_pages:
            try:
                # Add page parameter to URL and apply filters if provided
                current_url = build_linkedin_url(query_params)
                if filters:
                    filter_params = "&".join(f"{key}={value}" for key, value in filters.items())
                    current_url += f"&{filter_params}"
                if page > 1:
                    current_url += f"&page={page}"
                
                driver.get(current_url)
                time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
                
                # Wait for results with timeout handling
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "reusable-search__result-container"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for results on page {page}")
                    break

                results = driver.find_elements(By.CLASS_NAME, "reusable-search__result-container")
                if not results:
                    break

                for result in results:
                    try:
                        profile = {
                            "name": result.find_element(By.CSS_SELECTOR, ".actor-name").text,
                            "title": result.find_element(By.CSS_SELECTOR, ".subline-level-1").text,
                            "location": result.find_element(By.CSS_SELECTOR, ".subline-level-2").text,
                            "profile_url": result.find_element(By.CSS_SELECTOR, ".app-aware-link").get_attribute("href")
                        }
                        if profile not in profiles:  # Avoid duplicates
                            profiles.append(profile)
                    except Exception as e:
                        logger.warning(f"Error parsing profile: {e}")
                        continue

                page += 1
                time.sleep(random.uniform(1, 2))  # Random delay between pages
                
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                break

        return profiles
    finally:
        driver.quit()