import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

// Stands in for a screen whose ticket has not landed yet, so every
// navigation item already opens its own route (FC-203).
// children: entry points that already work there (the fridge card, FC-206).
export default function PlaceholderPage({
  titleKey,
  children,
}: {
  titleKey: string;
  children?: ReactNode;
}) {
  const { t } = useTranslation();

  return (
    <section className="fc-screen" aria-labelledby="placeholder-title">
      <h1 id="placeholder-title" className="fc-screen__title">
        {t(titleKey)}
      </h1>
      <p className="fc-screen__text">{t('shell.placeholder.text')}</p>
      {children}
    </section>
  );
}
