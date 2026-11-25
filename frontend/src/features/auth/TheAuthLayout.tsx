import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import mascotUrl from '../../assets/mascot-fridge.png';
import AuthIcon from './AuthIcon';

type TheAuthLayoutProps = {
  // Desktop brand half (DLogin / DPhone / DForgot); hidden on phones.
  brandTitle: string;
  brandText?: string;
  brandSteps?: { title: string; items: string[] };
  isRoot?: boolean;
  children: ReactNode;
};

export default function TheAuthLayout({
  brandTitle,
  brandText,
  brandSteps,
  isRoot = false,
  children,
}: TheAuthLayoutProps) {
  const { t } = useTranslation();

  return (
    <div className="fc-auth">
      <aside className="fc-auth__brand" aria-hidden="true">
        <div className="fc-auth__logo">
          <span className="fc-auth__logomark">
            <AuthIcon name="home" />
          </span>
          {t('app.name')}
        </div>
        {brandSteps ? (
          <div className="fc-auth__brandsteps">
            <span className="fc-auth__infotitle">{brandSteps.title}</span>
            <ol>
              {brandSteps.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </div>
        ) : (
          <div className="fc-auth__brandart">
            <img src={mascotUrl} alt="" />
          </div>
        )}
        <div className="fc-auth__brandcopy">
          <p className="fc-auth__brandtitle">{brandTitle}</p>
          {brandText && <p className="fc-auth__brandtext">{brandText}</p>}
        </div>
      </aside>
      <main className="fc-auth__main">
        <div className={isRoot ? 'fc-auth__form fc-auth__form--root' : 'fc-auth__form'}>
          {children}
        </div>
      </main>
    </div>
  );
}
