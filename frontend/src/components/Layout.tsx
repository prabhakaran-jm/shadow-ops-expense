import { Outlet } from 'react-router-dom'
import styles from './Layout.module.css'

export default function Layout() {
  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>◇</span>
          <span className={styles.logoText}>Shadow Ops</span>
        </div>
        <nav className={styles.nav}>
          <a href="/" className={styles.navItemActive}>Dashboard</a>
        </nav>
      </aside>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
