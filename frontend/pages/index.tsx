import Link from 'next/link';
import styles from '../styles/index.module.scss';

export default function Home() {
  return (
    <div className={styles.container}>
      <h1>LinkedIn Scraper</h1>
      <p>Test the LinkedIn scraper backend functionality.</p>
      <div className={styles.buttonGroup}>
        <Link href="/profiles">
          <button>Profile Scraper</button>
        </Link>
        <Link href="/comments">
          <button>Comment Scraper</button>
        </Link>
      </div>
    </div>
  );
}