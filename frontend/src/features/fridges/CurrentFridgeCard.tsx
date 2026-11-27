import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';

import mascotUrl from '../../assets/mascot-fridge.png';
import NavIcon from '../../components/layout/NavIcon';
import { isPathActive } from '../../components/layout/navItems';
import { APP_PATHS } from '../../routes/paths';
import { useCurrentFridge } from './useFridges';

// The current fridge (DSide card): name and members; opens the fridge list.
// Lives in the desktop sidebar and, until FC-406 / FC-607, on the home and
// Profile placeholders so phones can switch too.
export default function CurrentFridgeCard() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const fridge = useCurrentFridge();

  return (
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
  );
}
