/**
 * UC2 test: NewVisitForm component (with skill)
 *  - client-side validation: missing date, missing description,
 *    future date, too-long description
 *  - a11y: labels, aria-invalid, aria-describedby, role="alert"
 *  - submit: success path (POST returns 201), error path
 *  - busy state on submit
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { axe } from 'jest-axe';
import { NewVisitForm } from '../src/components/NewVisitForm.jsx';

describe('NewVisitForm (UC2, with frontend-implementation skill)', () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('has no axe a11y violations', async () => {
        const { container } = render(<NewVisitForm petId={8} />);
        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('has labels for every input', () => {
        render(<NewVisitForm petId={8} />);
        const dateInput = screen.getByLabelText(/visit date/i);
        const descInput = screen.getByLabelText(/description/i);
        expect(dateInput).toBeInTheDocument();
        expect(descInput).toBeInTheDocument();
    });

    it('shows validation error when description is empty', async () => {
        const user = userEvent.setup();
        render(<NewVisitForm petId={8} />);
        // Clear the date to force a future-date error... no, clear the description
        const descInput = screen.getByLabelText(/description/i);
        await user.clear(descInput);
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        expect(
            await screen.findByText(/description is required/i)
        ).toBeInTheDocument();
        // fetch should NOT have been called
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('shows validation error when date is in the future', async () => {
        const user = userEvent.setup();
        render(<NewVisitForm petId={8} />);
        const dateInput = screen.getByLabelText(/visit date/i);
        await user.clear(dateInput);
        await user.type(dateInput, '2099-01-01');
        const descInput = screen.getByLabelText(/description/i);
        await user.type(descInput, 'test visit');
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        expect(
            await screen.findByText(/date cannot be in the future/i)
        ).toBeInTheDocument();
    });

    it('shows error when description is too long', async () => {
        const user = userEvent.setup();
        // Mock fetch to never call (we just want to test the
        // client-side validation, not the network call)
        global.fetch = vi.fn();
        render(<NewVisitForm petId={8} />);
        const descInput = screen.getByLabelText(/description/i);
        // Bypass the maxLength=255 native limit by setting the
        // value directly via the React-aware path.
        // Simulate paste of 256 chars:
        const longVal = 'x'.repeat(256);
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype,
            'value'
        ).set;
        nativeInputValueSetter.call(descInput, longVal);
        descInput.dispatchEvent(new Event('input', { bubbles: true }));
        // Click submit
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        // The error should appear
        expect(
            await screen.findByText(/description must be 255 characters or fewer/i)
        ).toBeInTheDocument();
        // fetch should NOT have been called (validation failed first)
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('aria-invalid and aria-describedby set on error', async () => {
        const user = userEvent.setup();
        render(<NewVisitForm petId={8} />);
        const descInput = screen.getByLabelText(/description/i);
        await user.clear(descInput);
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        await waitFor(() => {
            expect(descInput).toHaveAttribute('aria-invalid', 'true');
            expect(descInput).toHaveAttribute(
                'aria-describedby',
                'new-visit-description-error'
            );
        });
    });

    it('submits successfully and shows success status', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ id: 99 }),
        });
        const onVisitCreated = vi.fn();
        render(
            <NewVisitForm petId={8} onVisitCreated={onVisitCreated} />
        );
        const descInput = screen.getByLabelText(/description/i);
        await user.type(descInput, 'annual checkup');
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        // Two elements have "visit created" — the aria-live sr-only
        // one and the role="status" one. Both should be present.
        await waitFor(() => {
            expect(screen.getAllByText(/visit created/i).length).toBeGreaterThan(0);
        });
        expect(screen.getByRole('status')).toHaveTextContent(/visit created/i);
        expect(onVisitCreated).toHaveBeenCalled();
        // Description was cleared
        expect(descInput).toHaveValue('');
    });

    it('shows server error on 4xx', async () => {
        const user = userEvent.setup();
        global.fetch.mockResolvedValue({
            ok: false,
            json: async () => ({ error: 'petId must be a positive integer' }),
        });
        render(<NewVisitForm petId={8} />);
        const descInput = screen.getByLabelText(/description/i);
        await user.type(descInput, 'test');
        await user.click(screen.getByRole('button', { name: /save visit/i }));
        expect(
            await screen.findByText(/could not save: petId must be a positive integer/i)
        ).toBeInTheDocument();
    });

    it('disables button while submitting', async () => {
        const user = userEvent.setup();
        // Never resolve to keep submitting state
        global.fetch.mockReturnValue(new Promise(() => {}));
        render(<NewVisitForm petId={8} />);
        const descInput = screen.getByLabelText(/description/i);
        await user.type(descInput, 'test');
        const submitBtn = screen.getByRole('button', { name: /save visit/i });
        await user.click(submitBtn);
        // Button text changes
        await waitFor(() => {
            expect(submitBtn).toHaveTextContent(/saving/i);
        });
        expect(submitBtn).toBeDisabled();
    });
});
