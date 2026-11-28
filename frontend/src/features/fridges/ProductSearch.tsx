import { useId, useState, type KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';

import type { ProductSuggestion } from '../../api/productsTypes';
import { PRODUCT_SEARCH_MAX_LENGTH } from '../../api/productsTypes';
import ProductSearchOption from './ProductSearchOption';
import { useProductSuggestions } from './useProductSuggestions';

type ProductSearchProps = {
  fridgeId: string;
  // Hidden label, read by screen readers (the field has none on screen).
  label: string;
  placeholder?: string;
  // Enter or a tap on a suggestion: open the item or the add form with it.
  onSelect: (suggestion: ProductSuggestion) => void;
  // Enter with no suggestion chosen: open the add form with the typed name.
  onSubmit: (text: string) => void;
};

const NO_OPTION = -1;

// Hidden on screen, read aloud (the search field has no visible label).
const VISUALLY_HIDDEN = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
  whiteSpace: 'nowrap',
} as const;

// The search field (fc-search) with suggestions from the first letter,
// asked 200 ms after the typing pauses. Keyboard: arrows move, Enter picks,
// Escape closes. Board: Fridge (v2, categories and search), DFridge.
export default function ProductSearch({
  fridgeId,
  label,
  placeholder,
  onSelect,
  onSubmit,
}: ProductSearchProps) {
  const { t } = useTranslation();
  const inputId = useId();
  const listId = useId();
  const [text, setText] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(NO_OPTION);
  const { suggestions, isLoading, isError, hasSettled } = useProductSuggestions(fridgeId, text);

  const hasText = text.trim().length > 0;
  const isListShown = isOpen && hasText && suggestions.length > 0;
  const canShowMessage = isOpen && hasText && !isListShown;
  const message = !canShowMessage
    ? null
    : isError
      ? t('productSearch.error')
      : hasSettled
        ? t('productSearch.empty')
        : null;

  function optionId(index: number): string {
    return `${listId}-${index}`;
  }

  function reset() {
    setText('');
    setIsOpen(false);
    setActiveIndex(NO_OPTION);
  }

  function choose(suggestion: ProductSuggestion) {
    onSelect(suggestion);
    reset();
  }

  function handleChange(value: string) {
    setText(value);
    setIsOpen(true);
    setActiveIndex(NO_OPTION);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' && suggestions.length > 0) {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((index) => (index + 1) % suggestions.length);
    } else if (event.key === 'ArrowUp' && suggestions.length > 0) {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((index) => (index <= 0 ? suggestions.length - 1 : index - 1));
    } else if (event.key === 'Escape') {
      setIsOpen(false);
      setActiveIndex(NO_OPTION);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const active = isListShown ? suggestions[activeIndex] : undefined;
      if (active) {
        choose(active);
      } else if (hasText) {
        onSubmit(text.trim());
        reset();
      }
    }
  }

  return (
    <div style={{ position: 'relative' }}>
      <label htmlFor={inputId} style={VISUALLY_HIDDEN}>
        {label}
      </label>
      <div className="fc-search">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-4-4" />
        </svg>
        <input
          id={inputId}
          type="text"
          role="combobox"
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={isListShown}
          aria-controls={listId}
          aria-activedescendant={
            isListShown && activeIndex >= 0 ? optionId(activeIndex) : undefined
          }
          aria-busy={isLoading}
          maxLength={PRODUCT_SEARCH_MAX_LENGTH}
          placeholder={placeholder}
          value={text}
          // 16 px, so mobile browsers do not zoom in.
          style={{ fontSize: '16px' }}
          onChange={(event) => handleChange(event.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setIsOpen(false)}
        />
      </div>
      <ul
        id={listId}
        role="listbox"
        aria-label={label}
        className="fc-list"
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          zIndex: 10,
          marginTop: 'var(--space-8)',
          boxShadow: 'var(--shadow-sheet)',
          listStyle: 'none',
          display: isListShown ? 'block' : 'none',
        }}
      >
        {isListShown
          ? suggestions.map((suggestion, index) => (
              <ProductSearchOption
                key={`${suggestion.source}-${suggestion.name}-${suggestion.unit}`}
                id={optionId(index)}
                suggestion={suggestion}
                isActive={index === activeIndex}
                onSelect={() => choose(suggestion)}
                onHover={() => setActiveIndex(index)}
              />
            ))
          : null}
      </ul>
      {message ? (
        <p
          role="status"
          style={{
            margin: 'var(--space-8) 0 0',
            fontSize: '13px',
            fontWeight: 600,
            color: isError ? 'var(--danger)' : 'var(--text-muted)',
          }}
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
