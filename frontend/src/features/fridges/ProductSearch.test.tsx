import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import type { ProductSuggestion } from '../../api/productsTypes';
import ProductSearch from './ProductSearch';

const MILK: ProductSuggestion = {
  source: 'catalog',
  name: 'молоко',
  unit: 'l',
  category: 'dairy',
  catalogProduct: null,
};
const CARROT: ProductSuggestion = {
  source: 'fridge',
  name: 'морква',
  unit: 'kg',
  category: 'veg',
  catalogProduct: null,
};

const { suggestProducts } = vi.hoisted(() => ({ suggestProducts: vi.fn() }));
vi.mock('../../api/products', () => ({ productsApi: { suggestProducts } }));

function renderSearch(onSelect = vi.fn(), onSubmit = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ProductSearch
        fridgeId="fridge-1"
        label="Пошук продукту"
        onSelect={onSelect}
        onSubmit={onSubmit}
      />
    </QueryClientProvider>,
  );
  const input = screen.getByRole('combobox', { name: 'Пошук продукту' });
  return { onSelect, onSubmit, input };
}

describe('ProductSearch', () => {
  beforeEach(() => {
    suggestProducts.mockReset();
    suggestProducts.mockResolvedValue([MILK, CARROT]);
  });
  afterEach(cleanup);

  it('shows молоко and морква after typing «мо»', async () => {
    const { input } = renderSearch();
    fireEvent.change(input, { target: { value: 'мо' } });
    expect(await screen.findByRole('option', { name: /молоко/ })).toBeTruthy();
    expect(screen.getByRole('option', { name: /морква/ })).toBeTruthy();
  });

  it('sends one request for fast typing', async () => {
    const { input } = renderSearch();
    fireEvent.change(input, { target: { value: 'м' } });
    fireEvent.change(input, { target: { value: 'мо' } });
    fireEvent.change(input, { target: { value: 'мол' } });
    await screen.findByRole('option', { name: /молоко/ });
    expect(suggestProducts).toHaveBeenCalledTimes(1);
    expect(suggestProducts).toHaveBeenCalledWith('fridge-1', 'мол');
  });

  it('picks with the keyboard: arrow down, then Enter', async () => {
    const { input, onSelect } = renderSearch();
    fireEvent.change(input, { target: { value: 'мо' } });
    await screen.findByRole('option', { name: /молоко/ });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onSelect).toHaveBeenCalledWith(CARROT);
    expect((input as HTMLInputElement).value).toBe('');
  });

  it('picks with a tap', async () => {
    const { input, onSelect } = renderSearch();
    fireEvent.change(input, { target: { value: 'мо' } });
    fireEvent.click(await screen.findByRole('option', { name: /молоко/ }));
    expect(onSelect).toHaveBeenCalledWith(MILK);
  });

  it('opens the add form with the typed text on Enter without a choice', async () => {
    suggestProducts.mockResolvedValue([]);
    const { input, onSubmit, onSelect } = renderSearch();
    fireEvent.change(input, { target: { value: ' кефір ' } });
    await waitFor(() => expect(suggestProducts).toHaveBeenCalled());
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onSubmit).toHaveBeenCalledWith('кефір');
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('closes the list on Escape', async () => {
    const { input } = renderSearch();
    fireEvent.change(input, { target: { value: 'мо' } });
    await screen.findByRole('option', { name: /молоко/ });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('option')).toBeNull();
  });
});
