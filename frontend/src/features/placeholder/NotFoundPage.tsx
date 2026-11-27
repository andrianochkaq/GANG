import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { APP_PATHS } from '../../routes/paths';

// Any path the app does not know, inside the shell so the nav stays usable.
export default function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <section className="fc-screen" aria-labelledby="not-found-title">
      <h1 id="not-found-title" className="fc-screen__title">
        {t('shell.notFound.title')}
      </h1>
      <p className="fc-screen__text">{t('shell.notFound.text')}</p>
      <Link to={APP_PATHS.home} className="fc-btn fc-btn--primary fc-btn--block">
        {t('shell.notFound.home')}
      </Link>
    </section>
  );
}
