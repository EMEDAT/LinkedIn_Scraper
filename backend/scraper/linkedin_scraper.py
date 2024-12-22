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
from flask import Flask, request, jsonify
from flask_cors import CORS
from .utils import init_selenium_driver
import logging
import time
import random
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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

def build_linkedin_url(query_params: Dict) -> str:
    """
    Build LinkedIn search URL from query parameters.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = [f"{key}={requests.utils.quote(str(value))}" for key, value in query_params.items() if value]
    return base_url + "&".join(params)

def scrape_linkedin_profiles(query_params: Dict, cookie: str) -> List[Dict]:
    """
    Scrape LinkedIn profiles using Selenium with improved error handling and rate limiting.
    """
    driver = init_selenium_driver()
    profiles = []
    page = 1
    max_pages = 3  # Adjust based on your needs
    
    try:
        if not login_with_cookie(driver, cookie):
            return profiles

        while page <= max_pages:
            try:
                # Add page parameter to URL
                current_url = build_linkedin_url(query_params)
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

# API Endpoints
@app.route('/search', methods=['POST'])
def search_profiles():
    try:
        data = request.json
        query = data.get('query')
        cookie = data.get('cookie')

        if not query or not cookie:
            return jsonify({'error': 'Query and LinkedIn cookie are required'}), 400

        profiles = scrape_linkedin_profiles(query, cookie)
        return jsonify({
            'status': 'success',
            'profile_count': len(profiles),
            'profiles': profiles
        })
    except Exception as e:
        logger.error(f"Error in /search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/comments', methods=['POST'])
def fetch_comments():
    try:
        data = request.json
        post_url = data.get('url')
        cookie = data.get('cookie')

        if not post_url or not cookie:
            return jsonify({'error': 'Post URL and LinkedIn cookie are required'}), 400

        comments = scrape_comments_from_post(post_url, cookie)
        return jsonify({
            'status': 'success',
            'comment_count': len(comments),
            'comments': comments
        })
    except Exception as e:
        logger.error(f"Error in /comments: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)