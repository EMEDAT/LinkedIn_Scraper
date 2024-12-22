import Link from 'next/link';
import styles from '../styles/Header.module.scss';

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <h1>LinkedIn Scraper</h1>
        <nav>
          <ul className={styles.navLinks}>
            <li>
              <Link href="/">Home</Link>
            </li>
            <li>
              <Link href="/profiles">Profiles</Link>
            </li>
            <li>
              <Link href="/comments">Comments</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}