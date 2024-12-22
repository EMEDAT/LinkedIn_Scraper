import { useState } from 'react';
import api from '../utils/api';
import styles from '../styles/comments.module.scss';

export default function Comments() {
  const [url, setUrl] = useState('');
  const [cookies, setCookies] = useState('');
  const [result, setResult] = useState<any>(null);

  const fetchComments = async (retries = 3) => {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await api.post('/comments', { url, cookies });
        setResult(response);
        break;
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
      }
    }
  };

  return (
    <div className={styles.container}>
      <h1>LinkedIn Comment Scraper</h1>
      <div className={styles.inputGroup}>
        <input
          type="text"
          placeholder="Enter LinkedIn post URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <input
          type="text"
          placeholder="Enter your LinkedIn cookies"
          value={cookies}
          onChange={(e) => setCookies(e.target.value)}
        />
      </div>
      <button className={styles.button} onClick={() => fetchComments()}>Scrape Comments</button>


      {result && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Result:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}