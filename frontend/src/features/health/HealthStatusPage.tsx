import { useTranslation } from 'react-i18next';

import HealthStatusPageRow from './HealthStatusPageRow';
import { useHealthStatus } from './useHealthStatus';

export default function HealthStatusPage() {
  const { t } = useTranslation();
  const { data, isPending, isError } = useHealthStatus();

  return (
    <section className="fc-screen">
      <h1 className="fc-header__title">{t('app.name')}</h1>
      {isPending && (
        <div className="fc-skeleton" aria-busy="true">
          <span className="fc-sr">{t('health.loading')}</span>
        </div>
      )}
      {isError && (
        <p className="fc-health__error" role="alert">
          {t('health.loadError')}
        </p>
      )}
      {data && (
        <section className="fc-card" aria-labelledby="health-title">
          <div className="fc-card__head">
            <h2 id="health-title" className="fc-card__title">
              {t('health.title')}
            </h2>
          </div>
          <p className="fc-health__meta">{t('health.subtitle')}</p>
          <HealthStatusPageRow label={t('health.database')} status={data.db} />
          <HealthStatusPageRow label={t('health.redis')} status={data.redis} />
        </section>
      )}
    </section>
  );
}
