import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialization
cred = credentials.Certificate("C:/Users/USER/Desktop/INTERVIEWS/LinkedIn_Scraper/backend/firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def save_to_firebase(data):
    """
    Save scraped data to Firebase.
    """
    for profile in data:
        db.collection('linkedin_profiles').add(profile)

def fetch_data():
    """
    Fetch data from Firebase.
    """
    docs = db.collection('linkedin_profiles').stream()
    return [doc.to_dict() for doc in docs]