import re
import dns.resolver
import logging
import csv
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_selenium_driver() -> webdriver.Chrome:
    """
    Initialize Selenium WebDriver with options and WebDriver Manager.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-ipv6")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_with_cookie(driver, cookie: str):
    """
    Log in to LinkedIn using cookies.
    """
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({"name": "li_at", "value": cookie})
    driver.refresh()
    logger.info("Logged in to LinkedIn using cookies")

def build_linkedin_url(query_params: Dict) -> str:
    """
    Build LinkedIn search URL from query parameters.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = [f"{key}={value}" for key, value in query_params.items() if value]
    return base_url + "&".join(params)

def validate_email(email: str, verify_dns: bool = True) -> bool:
    """
    Validate email format and optionally verify domain using DNS lookup.
    """
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Removed extra backslash
    if not re.match(regex, email):
        logger.info(f"Email {email} failed regex validation")
        return False

    if verify_dns:
        try:
            domain = email.split('@')[1]
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2
            resolver.lifetime = 2
            resolver.resolve(domain, 'MX')
            logger.info(f"Email {email} passed validation with DNS verification")
            return True
        except Exception as e:
            logger.info(f"Email {email} failed DNS validation: {str(e)}")
            return False

    logger.info(f"Email {email} passed basic validation (DNS verification skipped)")
    return True

def export_to_csv(profiles: List[Dict], filename: str) -> None:
    """
    Export profiles to CSV format with error handling.
    """
    fieldnames = ['name', 'title', 'location', 'profile_url']
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for profile in profiles:
                writer.writerow({k: profile.get(k, '') for k in fieldnames})
        logger.info(f"Successfully exported profiles to {filename}")
    except IOError as e:
        logger.error(f"Failed to export to CSV: {str(e)}")
        raise

def ensure_gdpr_compliance(profile_data: Dict) -> Dict:
    """
    Ensure GDPR compliance for scraped data.
    """
    try:
        gdpr_compliant_data = {
            'data_source': profile_data.get('data_source', 'LinkedIn Public Profile'),
            'collection_date': profile_data.get('collection_date', datetime.now().isoformat()),
            'legal_basis': 'Legitimate Interest',
            'retention_period': '30 days',
            'profile_data': {k: v for k, v in profile_data.items() if k not in ['collection_date', 'data_source']}
        }

        if 'email' in profile_data:
            import hashlib
            email_hash = hashlib.sha256(profile_data['email'].encode()).hexdigest()
            gdpr_compliant_data['profile_data']['email_hash'] = email_hash
            del gdpr_compliant_data['profile_data']['email']

        logger.info("Successfully applied GDPR compliance transformations")
        return gdpr_compliant_data
    except Exception as e:
        logger.error(f"Failed to ensure GDPR compliance: {str(e)}")
        raise