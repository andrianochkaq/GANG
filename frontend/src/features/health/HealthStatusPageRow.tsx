import { useTranslation } from 'react-i18next';

import type { ServiceStatus } from '../../api/health';

type HealthStatusPageRowProps = {
  label: string;
  status: ServiceStatus;
};

export default function HealthStatusPageRow({ label, status }: HealthStatusPageRowProps) {
  const { t } = useTranslation();
  const isOk = status === 'ok';
  const valueClass = isOk ? 'fc-health__value' : 'fc-health__value fc-health__value--error';

  return (
    <div className="fc-health__row">
      <span>{label}</span>
      <span className={valueClass}>{t(isOk ? 'health.statusOk' : 'health.statusError')}</span>
    </div>
  );
}
