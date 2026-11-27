import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';

import mascotUrl from '../../assets/mascot-fridge.png';
import { APP_PATHS } from '../../routes/paths';
import NavIcon from './NavIcon';
import { isPathActive, type NavItem } from './navItems';

export type SidebarFridge = {
  name: string;
  memberCount: number;
};

type SidebarProps = {
  items: NavItem[];
  // Filled once the fridge (FC-206) and shopping (FC-402) APIs exist; until
  // then the card shows a neutral title and the count stays hidden.
  fridge?: SidebarFridge;
  openShoppingCount?: number;
};

// DSide: wordmark, the four tab roots, the current-fridge card and Shopping.
export default function Sidebar({ items, fridge, openShoppingCount }: SidebarProps) {
  const { t } = useTranslation();
  const { pathname } = useLocation();

  return (
    <nav className="fc-sidebar" aria-label={t('shell.navLabel')}>
      <Link to={APP_PATHS.home} className="fc-sidebar__brand">
        <span className="fc-sidebar__logo">
          <NavIcon name="home" />
        </span>
        {t('app.name')}
      </Link>

      <div className="fc-sidebar__items">
        {items.map((item) => (
          <Link
            key={item.id}
            to={item.path}
            className="fc-sideitem"
            aria-current={isPathActive(item.path, pathname) ? 'page' : undefined}
          >
            <NavIcon name={item.id} />
            {t(item.labelKey)}
          </Link>
        ))}
      </div>

      <Link
        to={APP_PATHS.fridges}
        className="fc-fridgecard"
        aria-current={isPathActive(APP_PATHS.fridges, pathname) ? 'page' : undefined}
      >
        <img src={mascotUrl} alt="" />
        <span className="fc-fridgecard__text">
          <span className="fc-fridgecard__name">
            {fridge ? fridge.name : t('shell.fridgeCard.fallbackName')}
          </span>
          <span className="fc-fridgecard__meta">
            {fridge
              ? t('shell.fridgeCard.members', { count: fridge.memberCount })
              : t('shell.fridgeCard.change')}
          </span>
        </span>
        <NavIcon name="chevron" />
      </Link>

      <Link
        to={APP_PATHS.shopping}
        className="fc-sidebar__shopping"
        aria-current={isPathActive(APP_PATHS.shopping, pathname) ? 'page' : undefined}
      >
        <NavIcon name="cart" />
        <span>{t('shell.nav.shopping')}</span>
        {openShoppingCount !== undefined && openShoppingCount > 0 && (
          <span className="fc-sidebar__count">
            <span aria-hidden="true">{openShoppingCount}</span>
            <span className="fc-sr">{t('shell.shoppingCount', { count: openShoppingCount })}</span>
          </span>
        )}
      </Link>
    </nav>
  );
}
