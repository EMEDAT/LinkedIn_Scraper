import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
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

def scrape_comments_from_post(post_url: str, cookie: str) -> List[Dict]:
    """
    Scrape comments from a LinkedIn post with improved loading and pagination.
    """
    driver = init_selenium_driver()
    comments = []

    try:
        if not login_with_cookie(driver, cookie):
            return comments

        driver.get(post_url)
        time.sleep(3)  # Initial wait for content to load

        # Scroll and load more comments
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Click "Load more" button if present
            try:
                load_more = driver.find_elements(By.CSS_SELECTOR, "button.comments-comments-list__load-more-comments-button")
                if load_more:
                    driver.execute_script("arguments[0].click();", load_more[0])
                    time.sleep(2)
            except Exception:
                pass

            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extract comments
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "comments-comment-item"))
            )

            results = driver.find_elements(By.CLASS_NAME, "comments-comment-item")
            for comment in results:
                try:
                    comment_data = {
                        "name": comment.find_element(By.CLASS_NAME, "comments-post-meta__name-text").text,
                        "comment": comment.find_element(By.CLASS_NAME, "comments-comment-item__main-content").text,
                        "timestamp": comment.find_element(By.CLASS_NAME, "comments-comment-item__timestamp").text,
                        "likes": _get_comment_likes(comment)
                    }
                    if comment_data not in comments:  # Avoid duplicates
                        comments.append(comment_data)
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.warning(f"Error parsing comment: {e}")
                    continue

        except TimeoutException:
            logger.warning("Timeout waiting for comments to load")

        return comments
    finally:
        driver.quit()

def _get_comment_likes(comment_element) -> int:
    """Helper function to extract comment likes count"""
    try:
        likes_element = comment_element.find_element(By.CSS_SELECTOR, ".comments-comment-social-bar__social-counts")
        likes_text = likes_element.text
        return int(''.join(filter(str.isdigit, likes_text)) or '0')
    except:
        return 0
