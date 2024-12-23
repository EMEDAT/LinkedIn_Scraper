
# LinkedIn Scraper

A web application that automates the extraction of publicly available LinkedIn data, including profiles and post comments, using AI-powered search queries.

---

## Installation

### Backend Setup
1. Add your Firebase service account key as `firebase_key.json`.
2. Navigate to the `backend` folder
3. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask server:
   ```bash
   python wsgi.py
   ```
   The server will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### Frontend Setup
1. Navigate to the `frontend` folder.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The app will be available at [http://localhost:3000](http://localhost:3000).

---

## Obtaining LinkedIn Cookies

To use the scraper, you need your LinkedIn cookies (specifically the `li_at` cookie). Follow these steps to get them:

1. Download the **EditThisCookies** Extension fom your Chrome Web Store
2. Open your browser and log in to your LinkedIn account.
3. On the Right top corner, beefore your download icon is your extension icon.
4. Select **EditThisCookies** from the list.
5. Look for the cookie named `li_at`. Copy its value.
6. Paste this value into the application where requested.

---

## Usage

### Scraping Profiles
1. Go to the `Profiles` page.
2. Enter a query (e.g., `Marketing managers in California`) and your LinkedIn cookies.
3. Click "Search Profiles" to retrieve results.

### Scraping Comments
1. Go to the `Comments` page.
2. Enter a LinkedIn post URL and your cookies.
3. Click "Scrape Comments" to retrieve comments from the post.

---

## API Endpoints

### `/search` (POST)
- **Description**: Fetch LinkedIn profiles based on user queries.
- **Payload**:
   ```json
   {
     "query": "Marketing managers in California",
     "cookies": "YOUR_LINKEDIN_COOKIE",
     "filters": {
       "location": "California",
       "industry": "Marketing"
     },
     "export_csv": true
   }
   ```

### `/comments` (POST)
- **Description**: Scrape comments from a LinkedIn post.
- **Payload**:
   ```json
   {
     "url": "https://www.linkedin.com/posts/example_post",
     "cookies": "YOUR_LINKEDIN_COOKIE"
   }
   ```

---

## Folder Structure

```lua
LinkedIn_Scraper
├── backend
│   ├── app.py
│   ├── scraper/
│   │   ├── linkedin_comment_scraper.py
│   │   ├── linkedin_profiles_scraper.py
│   │   ├── utils.py
│   ├── ai/
│   │   ├── query_processor.py
│   ├── database/
│   │   ├── firebase_client.py
│   ├── wsgi.py
│   ├── requirements.txt
│   └── firebase_key.json
├── frontend
│   ├── components/
│   │   ├── Footer.tsx
│   │   ├── Header.tsx
│   ├── pages/
│   │   ├── index.tsx
│   │   ├── profiles.tsx
│   │   ├── comments.tsx
│   ├── styles/
│   │   ├── globals.scss
│   ├── package.json
│   └── next.config.ts
```

---

## Notes on Compliance
This project scrapes publicly available data and does not bypass LinkedIn's authentication or violate terms of service. Ensure ethical usage and follow GDPR/CCPA guidelines.

---

## Future Improvements
- Add OAuth for secure authentication.
- Enhance UI with better pagination and progress tracking.
- Implement advanced AI-powered query handling.

---

## License
This project is licensed under [MIT License](LICENSE).
