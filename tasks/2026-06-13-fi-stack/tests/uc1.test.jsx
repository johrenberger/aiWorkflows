/**
 * UC1 test: PetVisitList component
 *  - renders loading state
 *  - renders error state on fetch failure
 *  - renders empty state when no visits
 *  - renders table on success
 *  - re-fetches when petId changes
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PetVisitList } from '../src/components/PetVisitList.jsx';

const PROXY_BASE = 'http://localhost:3001';

describe('PetVisitList (UC1, no skill baseline)', () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('shows loading state initially', () => {
        global.fetch.mockReturnValue(new Promise(() => {})); // never resolves
        render(<PetVisitList petId={8} />);
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders a table of visits on success', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({
                petId: 8,
                count: 2,
                visits: [
                    { id: 4, date: '2013-01-02', description: 'rabies shot' },
                    { id: 3, date: '2013-01-03', description: 'spayed' },
                ],
            }),
        });
        render(<PetVisitList petId={8} />);
        await waitFor(() => {
            expect(screen.getByText('rabies shot')).toBeInTheDocument();
        });
        expect(screen.getByText('spayed')).toBeInTheDocument();
        // Table has Date and Description columns
        expect(screen.getByText('Date')).toBeInTheDocument();
        expect(screen.getByText('Description')).toBeInTheDocument();
    });

    it('renders empty state when no visits', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ petId: 999, count: 0, visits: [] }),
        });
        render(<PetVisitList petId={999} />);
        await waitFor(() => {
            expect(screen.getByText(/no visits/i)).toBeInTheDocument();
        });
    });

    it('renders error state on fetch failure', async () => {
        global.fetch.mockRejectedValue(new Error('Network error'));
        render(<PetVisitList petId={8} />);
        await waitFor(() => {
            expect(screen.getByText(/error: network error/i)).toBeInTheDocument();
        });
    });

    it('re-fetches when petId changes', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ petId: 8, count: 0, visits: [] }),
        });
        const { rerender } = render(<PetVisitList petId={8} />);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/proxy/pets/8/visits')
            );
        });
        global.fetch.mockClear();
        rerender(<PetVisitList petId={7} />);
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/proxy/pets/7/visits')
            );
        });
    });
});
