import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';

import NavIcon from './NavIcon';
import { isPathActive, type NavItem } from './navItems';

// Nav3: 76 px bar, icon in a 56×30 pill, label under it.
export default function BottomNav({ items }: { items: NavItem[] }) {
  const { t } = useTranslation();
  const { pathname } = useLocation();

  return (
    <nav className="fc-nav" aria-label={t('shell.navLabel')}>
      {items.map((item) => (
        <Link
          key={item.id}
          to={item.path}
          className="fc-navitem"
          aria-current={isPathActive(item.path, pathname) ? 'page' : undefined}
        >
          <span className="fc-navitem__pill">
            <NavIcon name={item.id} />
          </span>
          {t(item.labelKey)}
        </Link>
      ))}
    </nav>
  );
}
