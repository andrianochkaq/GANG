import { useTranslation } from 'react-i18next';

import { getAuthErrorMessageKey } from '../../api/authErrors';

type AuthErrorMessageProps = {
  error: unknown;
  id?: string;
};

// The error sentence next to the form that failed (design system: «Error»).
export default function AuthErrorMessage({ error, id }: AuthErrorMessageProps) {
  const { t } = useTranslation();
  if (!error) {
    return null;
  }
  const { key, detail } = getAuthErrorMessageKey(error);

  return (
    <p className="fc-field__error" role="alert" id={id}>
      {t(key, { detail })}
    </p>
  );
}
