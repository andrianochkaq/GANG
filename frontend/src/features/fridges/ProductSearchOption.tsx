import { useTranslation } from 'react-i18next';

import type { ProductSuggestion } from '../../api/productsTypes';

type ProductSearchOptionProps = {
  id: string;
  suggestion: ProductSuggestion;
  isActive: boolean;
  onSelect: () => void;
  onHover: () => void;
};

// One row of the dropdown (ListGroup row: title 15 / 600, meta 12).
export default function ProductSearchOption({
  id,
  suggestion,
  isActive,
  onSelect,
  onHover,
}: ProductSearchOptionProps) {
  const { t } = useTranslation();
  return (
    <li
      id={id}
      role="option"
      aria-selected={isActive}
      className="fc-listrow"
      style={{
        minHeight: 'var(--size-control-lg)',
        cursor: 'pointer',
        background: isActive ? 'var(--soft)' : 'transparent',
      }}
      // mousedown keeps the focus in the input, so the list stays open.
      onMouseDown={(event) => event.preventDefault()}
      onClick={onSelect}
      onMouseEnter={onHover}
    >
      <span className="fc-listrow__main">
        <span className="fc-listrow__title">{suggestion.name}</span>
        <span className="fc-listrow__meta">{t(`productSearch.source.${suggestion.source}`)}</span>
      </span>
    </li>
  );
}
