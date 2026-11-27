import { useId, useState, type FormEvent, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { getAuthErrorMessageKey } from '../../api/authErrors';
import { FRIDGE_NAME_MAX_LENGTH } from '../../api/fridgesTypes';

type FridgeNameFormProps = {
  label: string;
  submitLabel: string;
  initialName?: string;
  // Under the field, left of the buttons: members and products (Fridges board).
  meta?: ReactNode;
  isSaving: boolean;
  error: unknown;
  onSubmit: (name: string) => void;
  onCancel: () => void;
};

// The inline card that renames a fridge or names a new one.
export default function FridgeNameForm({
  label,
  submitLabel,
  initialName = '',
  meta,
  isSaving,
  error,
  onSubmit,
  onCancel,
}: FridgeNameFormProps) {
  const { t } = useTranslation();
  const inputId = useId();
  const errorId = useId();
  const [name, setName] = useState(initialName);
  const [isEmpty, setIsEmpty] = useState(false);

  const serverMessage = error ? getAuthErrorMessageKey(error) : null;
  const message = isEmpty
    ? t('fridges.nameRequired')
    : serverMessage
      ? t(serverMessage.key, { detail: serverMessage.detail })
      : null;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setIsEmpty(true);
      return;
    }
    onSubmit(trimmed);
  }

  return (
    <form className="fc-switcher__form" onSubmit={handleSubmit} noValidate>
      <div className="fc-field">
        <label htmlFor={inputId} className="fc-switcher__formlabel">
          {label}
        </label>
        <input
          id={inputId}
          className="fc-input fc-input--md"
          value={name}
          maxLength={FRIDGE_NAME_MAX_LENGTH}
          autoComplete="off"
          // The form opens on a tap, so the cursor goes straight into it.
          autoFocus
          aria-invalid={message ? true : undefined}
          aria-describedby={message ? errorId : undefined}
          onChange={(event) => {
            setName(event.target.value);
            setIsEmpty(false);
          }}
        />
        {message && (
          <p id={errorId} className="fc-field__error" role="alert">
            {message}
          </p>
        )}
      </div>
      <div className="fc-switcher__formfoot">
        <span className="fc-switcher__meta">{meta}</span>
        <div className="fc-switcher__actions">
          <button
            type="button"
            className="fc-btn fc-btn--sm fc-switcher__cancel"
            onClick={onCancel}
          >
            {t('fridges.cancel')}
          </button>
          <button type="submit" className="fc-btn fc-btn--sm fc-btn--primary" disabled={isSaving}>
            {submitLabel}
          </button>
        </div>
      </div>
    </form>
  );
}
