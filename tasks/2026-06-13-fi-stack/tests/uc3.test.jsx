/**
 * UC3 test: PetTypeFilter combobox (with skill)
 *  - renders input with combobox role
 *  - shows suggestions when typing
 *  - keyboard navigation: ArrowDown, ArrowUp, Enter, Escape
 *  - selection updates the input value
 *  - aria-expanded toggles
 *  - aria-activedescendant follows active option
 *  - empty state shows "No matches"
 *  - aria-live region announces results
 *  - no axe a11y violations
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { axe } from 'jest-axe';
import { PetTypeFilter } from '../src/components/PetTypeFilter.jsx';

const PROXY_BASE = 'http://localhost:3001';

describe('PetTypeFilter (UC3, with frontend-implementation skill)', () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.useRealTimers();
    });

    it('has no axe a11y violations', async () => {
        const { container } = render(<PetTypeFilter />);
        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('renders an input with role=combobox', () => {
        render(<PetTypeFilter />);
        const combobox = screen.getByRole('combobox');
        expect(combobox).toBeInTheDocument();
        expect(combobox).toHaveAttribute('aria-expanded', 'false');
    });

    it('aria-expanded becomes true when typing', async () => {
        const user = userEvent.setup();
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'Leo');
        // Listbox is hidden until debounced fetch resolves
        await waitFor(() => {
            expect(input).toHaveAttribute('aria-expanded', 'true');
        });
    });

    it('shows suggestions when fetch returns results', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                type: 'Leo',
                limit: 10,
                count: 2,
                pets: [
                    { id: 1, name: 'Leo', type: { name: 'cat' } },
                    { id: 7, name: 'Leo2', type: { name: 'cat' } },
                ],
            }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'Leo');
        // Wait past debounce
        await waitFor(() => {
            const listbox = screen.getByRole('listbox');
            const options = within(listbox).getAllByRole('option');
            expect(options.length).toBe(2);
        });
    });

    it('ArrowDown moves active descendant', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                pets: [
                    { id: 1, name: 'A', type: { name: 'cat' } },
                    { id: 2, name: 'B', type: { name: 'cat' } },
                ],
            }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'A');
        // Wait for fetch + listbox to appear
        await waitFor(() => {
            const lb = screen.getByRole('listbox');
            expect(within(lb).getAllByRole('option')).toHaveLength(2);
        });
        // First ArrowDown: -1 → 0
        await user.keyboard('{ArrowDown}');
        await waitFor(() => {
            expect(input).toHaveAttribute(
                'aria-activedescendant',
                expect.stringMatching(/-option-0$/)
            );
        });
        // Second ArrowDown: 0 → 1
        await user.keyboard('{ArrowDown}');
        await waitFor(() => {
            expect(input).toHaveAttribute(
                'aria-activedescendant',
                expect.stringMatching(/-option-1$/)
            );
        });
    });

    it('Enter selects the active suggestion', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                pets: [{ id: 1, name: 'SelectedPet', type: { name: 'cat' } }],
            }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'S');
        // Wait for fetch to be called (debounce 200ms)
        await waitFor(() => expect(global.fetch).toHaveBeenCalled(), { timeout: 1000 });
        // Wait for the actual data to appear (not just the loading state)
        await waitFor(() => {
            const lb = screen.getByRole('listbox');
            const options = within(lb).getAllByRole('option');
            const realPets = options.filter(
                (o) => !o.textContent.match(/loading|no matches/i)
            );
            expect(realPets.length).toBe(1);
        });
        // ArrowDown: -1 → 0
        await user.keyboard('{ArrowDown}');
        await waitFor(() => {
            expect(input).toHaveAttribute(
                'aria-activedescendant',
                expect.stringMatching(/-option-0$/)
            );
        });
        // Enter selects
        await user.keyboard('{Enter}');
        await waitFor(() => {
            expect(input).toHaveValue('SelectedPet');
        });
        // Listbox is closed
        await waitFor(() => {
            expect(input).toHaveAttribute('aria-expanded', 'false');
        });
        // Status region announces selection
        expect(screen.getByText(/selected: SelectedPet/i)).toBeInTheDocument();
    });

    it('Escape closes the listbox', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ pets: [{ id: 1, name: 'A', type: { name: 'cat' } }] }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'A');
        await waitFor(() => screen.getByRole('listbox'));
        await user.keyboard('{Escape}');
        await waitFor(() => {
            expect(input).toHaveAttribute('aria-expanded', 'false');
        });
    });

    it('shows "No matches" when results are empty', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ pets: [] }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'zzz');
        await waitFor(() => {
            expect(screen.getByText(/no matches/i)).toBeInTheDocument();
        });
    });

    it('does not call fetch when input is empty', async () => {
        render(<PetTypeFilter />);
        await waitFor(() => {
            expect(global.fetch).not.toHaveBeenCalled();
        });
    });

    it('debounces fetch (waits 200ms before calling)', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ pets: [] }),
        });
        render(<PetTypeFilter />);
        const input = screen.getByRole('combobox');
        await user.click(input);
        await user.type(input, 'L');
        // Immediately after typing, fetch should not have been called
        expect(global.fetch).not.toHaveBeenCalled();
        // Wait past debounce
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalled();
        });
    });
});
