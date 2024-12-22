import styles from '../styles/Footer.module.scss';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <p>© {new Date().getFullYear()} LinkedIn Scraper. All rights reserved.</p>
      </div>
    </footer>
  );
}