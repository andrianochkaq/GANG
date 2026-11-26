import { useRef } from 'react';
import type { KeyboardEvent } from 'react';

export type BaseColorPickerOption = {
  id: string;
  label: string;
  swatch: string;
};

type BaseColorPickerProps = {
  options: readonly BaseColorPickerOption[];
  value: string;
  onChange: (id: string) => void;
  label: string;
  isDisabled?: boolean;
};

const STEP_BY_KEY: Record<string, number> = {
  ArrowRight: 1,
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowUp: -1,
};

// Swatch grid (docs/design-system/components/ColorPicker.md): a radio group
// of 46 px rings with the colour name under each. Arrow keys move the
// selection, Home and End jump to the first and last colour.
export default function BaseColorPicker({
  options,
  value,
  onChange,
  label,
  isDisabled = false,
}: BaseColorPickerProps) {
  const swatchRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function selectAt(index: number) {
    const option = options[index];
    if (option) {
      onChange(option.id);
      swatchRefs.current[index]?.focus();
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (isDisabled || options.length === 0) {
      return;
    }
    const currentIndex = Math.max(
      0,
      options.findIndex((option) => option.id === value),
    );
    const step = STEP_BY_KEY[event.key];
    if (step !== undefined) {
      event.preventDefault();
      selectAt((currentIndex + step + options.length) % options.length);
    } else if (event.key === 'Home') {
      event.preventDefault();
      selectAt(0);
    } else if (event.key === 'End') {
      event.preventDefault();
      selectAt(options.length - 1);
    }
  }

  return (
    <div className="fc-palette" role="radiogroup" aria-label={label} onKeyDown={handleKeyDown}>
      {options.map((option, index) => {
        const isSelected = option.id === value;
        return (
          <button
            key={option.id}
            ref={(element) => {
              swatchRefs.current[index] = element;
            }}
            type="button"
            role="radio"
            className="fc-swatch"
            aria-checked={isSelected}
            aria-label={option.label}
            tabIndex={isSelected ? 0 : -1}
            disabled={isDisabled}
            onClick={() => onChange(option.id)}
          >
            <span className="fc-swatch__ring">
              <span className="fc-swatch__dot" style={{ background: option.swatch }} />
            </span>
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
