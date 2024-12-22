import { useState } from 'react';
import api from '../utils/api';
import styles from '../styles/profiles.module.scss';

export default function Profiles() {
  const [query, setQuery] = useState('');
  const [cookies, setCookies] = useState('');
  const [result, setResult] = useState<any>(null);

  const fetchProfiles = async () => {
    try {
      const response = await api.post('/search', { query, cookies });
      setResult(response); // Response is already unpacked by the interceptor
    } catch (error) {
      console.error('Error fetching profiles:', error);
      setResult({ error: 'Failed to fetch profiles' });
    }
  };

  return (
    <div className={styles.container}>
      <h1>LinkedIn Profile Scraper</h1>
      <div className={styles.inputGroup}>
        <input
          type="text"
          placeholder="Enter your query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <input
          type="text"
          placeholder="Enter your LinkedIn cookies"
          value={cookies}
          onChange={(e) => setCookies(e.target.value)}
        />
      </div>
      <button onClick={fetchProfiles}>Search Profiles</button>

      {result && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Result:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}