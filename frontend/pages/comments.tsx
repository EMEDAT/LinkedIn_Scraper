import { useState } from 'react';
import api from '../utils/api';
import styles from '../styles/comments.module.scss';

export default function Comments() {
  const [url, setUrl] = useState('');
  const [cookies, setCookies] = useState('');
  const [result, setResult] = useState<any>(null);

  const fetchComments = async () => {
    try {
      const response = await api.post('/comments', { url, cookies });
      setResult(response); // Response is already unpacked by the interceptor
    } catch (error) {
      console.error('Error fetching comments:', error);
      setResult({ error: 'Failed to fetch comments' });
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
      <button onClick={fetchComments}>Scrape Comments</button>

      {result && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Result:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}