import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import random
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 3.0):
    """Decorator to implement rate limiting between requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(random.uniform(min_delay, max_delay))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def build_linkedin_url(query_params: Dict) -> str:
    """
    Convert processed query parameters into a LinkedIn search URL.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = []
    
    mappings = {
        "keywords": "keywords",
        "title": "title",
        "location": "location",
        "industry": "industry",
        "company": "company"
    }
    
    for key, param in mappings.items():
        if query_params.get(key):
            params.append(f"{param}={requests.utils.quote(query_params[key])}")
    
    return base_url + "&".join(params)

@rate_limit_decorator()
def scrape_linkedin_profiles(query_params: Dict, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Scrape LinkedIn profiles based on structured query parameters.
    Implements rate limiting and error handling.
    """
    search_url = build_linkedin_url(query_params)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        profiles = []
        
        for profile in soup.select('.search-result__info'):
            try:
                profile_data = {
                    'name': profile.select_one('.actor-name').text.strip(),
                    'title': profile.select_one('.subline-level-1').text.strip(),
                    'location': profile.select_one('.subline-level-2').text.strip(),
                    'url': f"https://linkedin.com{profile.select_one('a')['href']}",
                    'collection_date': datetime.now().isoformat(),
                    'data_source': 'LinkedIn Public Profile'
                }
                profiles.append(profile_data)
            except AttributeError as e:
                logger.warning(f"Failed to parse profile: {str(e)}")
                continue
        
        if filters:
            profiles = apply_filters(profiles, filters)
            
        return remove_duplicates(profiles)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch LinkedIn profiles: {str(e)}")
        raise

def apply_filters(profiles: List[Dict], filters: Dict) -> List[Dict]:
    """
    Apply filters to the scraped profiles with improved filtering logic.
    """
    filtered_profiles = []
    for profile in profiles:
        matches_all_filters = True
        for key, value in filters.items():
            profile_value = profile.get(key, '').lower()
            filter_value = str(value).lower()
            
            if not (filter_value in profile_value):
                matches_all_filters = False
                break
                
        if matches_all_filters:
            filtered_profiles.append(profile)
            
    return filtered_profiles

def remove_duplicates(profiles: List[Dict]) -> List[Dict]:
    """
    Remove duplicate profiles based on URL and name.
    """
    seen = set()
    unique_profiles = []
    
    for profile in profiles:
        profile_key = (profile.get('url', ''), profile.get('name', ''))
        if profile_key not in seen:
            seen.add(profile_key)
            unique_profiles.append(profile)
    
    return unique_profiles

@rate_limit_decorator()
def scrape_comments_from_post(url: str, cookies: str) -> List[Dict]:
    """
    Scrape comments from a LinkedIn post with improved error handling.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cookie': cookies
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = []

        for comment in soup.select('.comments-comments-list__comment'):
            try:
                comment_data = {
                    'name': comment.select_one('.actor-name').text.strip(),
                    'comment': comment.select_one('.commentary').text.strip(),
                    'url': f"https://linkedin.com{comment.select_one('a')['href']}",
                    'collection_date': datetime.now().isoformat(),
                    'data_source': 'LinkedIn Comment'
                }
                comments.append(comment_data)
            except AttributeError as e:
                logger.warning(f"Failed to parse comment: {str(e)}")
                continue

        return comments
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch LinkedIn comments: {str(e)}")
        raise