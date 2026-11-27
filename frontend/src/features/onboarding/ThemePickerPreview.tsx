import { Trans, useTranslation } from 'react-i18next';

import mascotUrl from '../../assets/mascot-fridge.png';

type ThemePickerPreviewProps = {
  themeName: string;
};

// Live preview card of the colour screen (ColorPicker.md): the mascot on
// `soft`, two `soft` text bars and an `accent` button, all read from the
// themed CSS variables, so they change as soon as a swatch is chosen.
export default function ThemePickerPreview({ themeName }: ThemePickerPreviewProps) {
  const { t } = useTranslation();

  return (
    <div className="fc-card fc-themepreview">
      <div className="fc-themepreview__visual" aria-hidden="true">
        <div className="fc-themepreview__art">
          <img src={mascotUrl} alt="" />
        </div>
        <div className="fc-themepreview__text">
          <span className="fc-themepreview__bar" />
          <span className="fc-themepreview__bar fc-themepreview__bar--short" />
          <span className="fc-themepreview__button">{t('onboarding.color.previewButton')}</span>
        </div>
      </div>
      <p className="fc-themepreview__chosen" role="status">
        <Trans
          i18nKey="onboarding.color.chosen"
          values={{ name: themeName }}
          components={{ b: <b /> }}
        />
      </p>
    </div>
  );
}
