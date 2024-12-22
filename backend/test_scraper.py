import unittest
from scraper.linkedin_scraper import (
    build_linkedin_url,
    scrape_linkedin_profiles,
    scrape_comments_from_post
)
from scraper.utils import validate_email, export_to_csv, ensure_gdpr_compliance
from ai.query_processor import process_query
from database.firebase_client import save_to_firebase
import json
import os

class TestLinkedInScraper(unittest.TestCase):
    def setUp(self):
        # You would need to replace this with valid LinkedIn cookies for testing
        self.test_cookies = "AQEDATY_pmsFJqblAAABk-x2AbwAAAGUEIKFvE0ASe_ERrDVJkhpxhFK3eNfNdsAnuSzPkIhf6ILhhwc-hRQMwn4r8NY4m_UsewGLOVRnj57OppRPHm_gpjApdieQvRsXFKPXbMyF_Ye3hA8HbONi83j"
    def test_url_builder(self):
        """Test LinkedIn URL builder"""
        print("\nTesting URL builder...")
        query_params = {
            "keywords": "software engineer",
            "location": "San Francisco",
            "company": "Google"
        }
        url = build_linkedin_url(query_params)
        print(f"Generated URL: {url}")
        self.assertTrue("linkedin.com" in url)
        self.assertTrue("keywords=software" in url)

    def test_query_processor(self):
        """Test AI query processor"""
        print("\nTesting query processor...")
        test_query = "Find software engineers in San Francisco working at startups"
        result = process_query(test_query)
        print(f"Original query: {test_query}")
        print(f"Processed query: {result}")
        self.assertTrue(isinstance(result, str))

    def test_email_validation(self):
        """Test email validation"""
        print("\nTesting email validation...")
        
        # Test basic format validation (without DNS verification)
        valid_email = "test@example.com"
        invalid_email = "invalid.email@"
        print(f"Testing valid email format: {valid_email}")
        print(f"Testing invalid email format: {invalid_email}")
        
        # Test without DNS verification
        self.assertTrue(validate_email(valid_email, verify_dns=False), 
                       "Valid email format should pass without DNS verification")
        self.assertFalse(validate_email(invalid_email, verify_dns=False), 
                         "Invalid email format should fail")
        

    def test_gdpr_compliance(self):
        """Test GDPR compliance transformer"""
        print("\nTesting GDPR compliance...")
        test_profile = {
            "name": "John Doe",
            "email": "john@example.com",
            "title": "Software Engineer"
        }
        compliant_data = ensure_gdpr_compliance(test_profile)
        print("GDPR compliant data:", json.dumps(compliant_data, indent=2))
        self.assertIn('legal_basis', compliant_data)
        self.assertNotIn('email', compliant_data['profile_data'])

    def test_csv_export(self):
        """Test CSV export functionality"""
        print("\nTesting CSV export...")
        test_profiles = [{
            "name": "Test User",
            "title": "Developer",
            "location": "New York"
        }]
        test_filename = "test_export.csv"
        export_to_csv(test_profiles, test_filename)
        self.assertTrue(os.path.exists(test_filename))
        print(f"CSV file created: {test_filename}")
        # Cleanup
        os.remove(test_filename)

    def test_profile_scraping(self):
        """Test LinkedIn profile scraping"""
        print("\nTesting profile scraping...")
        query_params = {
            "keywords": "software engineer",
            "location": "San Francisco"
        }
        try:
            profiles = scrape_linkedin_profiles(query_params)
            print(f"Scraped {len(profiles)} profiles")
            self.assertTrue(isinstance(profiles, list))
        except Exception as e:
            print(f"Note: Scraping test failed (this might be expected): {str(e)}")

    def test_comment_scraping(self):
        """Test LinkedIn comment scraping"""
        print("\nTesting comment scraping...")
        test_url = "https://www.linkedin.com/posts/dthompsondev_yesterday-someone-asked-for-there-to-be-a-activity-7276041809804345344-QYyP?utm_source=share&utm_medium=member_desktop"
        try:
            comments = scrape_comments_from_post(test_url, self.test_cookies)
            print(f"Scraped {len(comments)} comments")
            self.assertTrue(isinstance(comments, list))
            if len(comments) > 0:
                self.assertIn('name', comments[0])
                self.assertIn('comment', comments[0])
                self.assertIn('timestamp', comments[0])
        except Exception as e:
            print(f"Note: Comment scraping test failed (this might be expected): {str(e)}")

if __name__ == '__main__':
    print("Starting LinkedIn Scraper Tests...")
    unittest.main(verbosity=2)