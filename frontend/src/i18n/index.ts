import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import uk from './uk.json';

export const DEFAULT_LANGUAGE = 'uk';

void i18n.use(initReactI18next).init({
  resources: { uk: { translation: uk } },
  lng: DEFAULT_LANGUAGE,
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false },
  returnNull: false,
  showSupportNotice: false,
});

export default i18n;
