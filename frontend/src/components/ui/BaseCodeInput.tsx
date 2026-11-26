import { useRef } from 'react';
import type { ClipboardEvent, KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';

export const CODE_LENGTH = 6;

const DIGIT_PATTERN = /\d/g;

type BaseCodeInputProps = {
  value: string;
  onChange: (value: string) => void;
  legend: string;
  isInvalid?: boolean;
  describedBy?: string;
  isDisabled?: boolean;
};

function keepDigits(text: string): string {
  return (text.match(DIGIT_PATTERN) ?? []).join('');
}

// Six 56 px cells (docs/design-system/components/CodeInput.md): typing moves
// to the next cell, a pasted code fills all, Backspace goes back.
export default function BaseCodeInput({
  value,
  onChange,
  legend,
  isInvalid = false,
  describedBy,
  isDisabled = false,
}: BaseCodeInputProps) {
  const { t } = useTranslation();
  const cellRefs = useRef<Array<HTMLInputElement | null>>([]);
  const digits = Array.from({ length: CODE_LENGTH }, (_cell, index) => value[index] ?? '');

  function focusCell(index: number) {
    const cell = cellRefs.current[Math.max(0, Math.min(index, CODE_LENGTH - 1))];
    cell?.focus();
    cell?.select();
  }

  function writeFrom(index: number, typed: string) {
    const next = (value.slice(0, index) + typed + value.slice(index + typed.length)).slice(
      0,
      CODE_LENGTH,
    );
    onChange(next);
    focusCell(index + typed.length);
  }

  function handleChange(index: number, text: string) {
    const typed = keepDigits(text);
    if (!typed) {
      return;
    }
    // A cell that already held a digit gets the new one.
    writeFrom(index, typed.length > 1 && digits[index] ? typed.slice(-1) : typed);
  }

  function handleKeyDown(index: number, event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Backspace') {
      event.preventDefault();
      const removeAt = digits[index] ? index : index - 1;
      if (removeAt >= 0) {
        onChange(value.slice(0, removeAt) + value.slice(removeAt + 1));
        focusCell(removeAt);
      }
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      focusCell(index - 1);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      focusCell(index + 1);
    }
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const pasted = keepDigits(event.clipboardData.getData('text'));
    if (pasted) {
      event.preventDefault();
      writeFrom(0, pasted);
    }
  }

  return (
    <fieldset className="fc-auth__fieldset" aria-describedby={describedBy}>
      <legend className="fc-auth__legend">{legend}</legend>
      <div className="fc-code">
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(cell) => {
              cellRefs.current[index] = cell;
            }}
            className={digit ? 'is-filled' : undefined}
            value={digit}
            onChange={(event) => handleChange(Math.min(index, value.length), event.target.value)}
            onKeyDown={(event) => handleKeyDown(index, event)}
            onPaste={handlePaste}
            onFocus={(event) => event.target.select()}
            inputMode="numeric"
            autoComplete={index === 0 ? 'one-time-code' : 'off'}
            maxLength={CODE_LENGTH}
            aria-label={t('auth.code.digit', { index: index + 1 })}
            aria-invalid={isInvalid || undefined}
            disabled={isDisabled}
          />
        ))}
      </div>
    </fieldset>
  );
}
