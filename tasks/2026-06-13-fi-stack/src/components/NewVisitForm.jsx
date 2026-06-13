/**
 * NewVisitForm — Use case #2 (with frontend-implementation skill)
 *
 * Skill-driven design choices (per react profile + a11y):
 *  - Functional component, hooks (matches "hooks + functional
 *    components" convention)
 *  - Controlled form inputs (date, description)
 *  - Client-side validation with explicit error messages
 *  - Errors surfaced via aria-describedby + role="alert"
 *  - Labels via <label htmlFor> (NOT placeholder-as-label)
 *  - Submit button shows busy/disabled state
 *  - aria-live="polite" on the status region for success
 *  - Keyboard navigation: native form controls handle this
 *  - Focus management: errors don't steal focus; status
 *    message is in an aria-live region
 *  - No new dependencies
 *  - No new state-management library
 *  - No framework swap
 */
import React, { useState } from 'react';

const PROXY_BASE = import.meta.env.VITE_PROXY_BASE || 'http://localhost:3001';

function validate({ date, description }) {
    const errors = {};
    if (!date) {
        errors.date = 'Date is required';
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        errors.date = 'Date must be in YYYY-MM-DD format';
    } else if (new Date(date) > new Date()) {
        errors.date = 'Date cannot be in the future';
    }
    if (!description || description.trim().length === 0) {
        errors.description = 'Description is required';
    } else if (description.length > 255) {
        errors.description = 'Description must be 255 characters or fewer';
    }
    return errors;
}

export function NewVisitForm({ petId, onVisitCreated }) {
    const [date, setDate] = useState(
        () => new Date().toISOString().slice(0, 10)
    );
    const [description, setDescription] = useState('');
    const [errors, setErrors] = useState({});
    const [serverError, setServerError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(null);

    const onSubmit = (e) => {
        e.preventDefault();
        setSuccess(null);
        setServerError(null);
        const validation = validate({ date, description });
        setErrors(validation);
        if (Object.keys(validation).length > 0) {
            return;
        }
        setSubmitting(true);
        fetch(`${PROXY_BASE}/proxy/visits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ petId, date, description }),
        })
            .then((r) => {
                if (!r.ok) {
                    return r.json().then((b) => {
                        throw new Error(b.error || `HTTP ${r.status}`);
                    });
                }
                return r.json();
            })
            .then(() => {
                setSuccess('Visit created');
                setDescription('');
                setSubmitting(false);
                if (onVisitCreated) onVisitCreated();
            })
            .catch((err) => {
                setServerError(err.message);
                setSubmitting(false);
            });
    };

    return (
        <form onSubmit={onSubmit} noValidate>
            <div className="field">
                <label htmlFor="new-visit-date">Visit date</label>
                <input
                    id="new-visit-date"
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    aria-describedby={errors.date ? 'new-visit-date-error' : undefined}
                    aria-invalid={errors.date ? 'true' : 'false'}
                    required
                />
                {errors.date && (
                    <p
                        id="new-visit-date-error"
                        className="error"
                        role="alert"
                    >
                        {errors.date}
                    </p>
                )}
            </div>
            <div className="field">
                <label htmlFor="new-visit-description">
                    Description
                </label>
                <textarea
                    id="new-visit-description"
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    aria-describedby={
                        errors.description
                            ? 'new-visit-description-error'
                            : undefined
                    }
                    aria-invalid={errors.description ? 'true' : 'false'}
                    maxLength={255}
                    required
                />
                {errors.description && (
                    <p
                        id="new-visit-description-error"
                        className="error"
                        role="alert"
                    >
                        {errors.description}
                    </p>
                )}
            </div>
            {serverError && (
                <p className="error" role="alert">
                    Could not save: {serverError}
                </p>
            )}
            <p aria-live="polite" className="sr-only">
                {success || ''}
            </p>
            {success && (
                <p role="status">{success}</p>
            )}
            <button
                type="submit"
                className="primary"
                disabled={submitting}
            >
                {submitting ? 'Saving...' : 'Save visit'}
            </button>
        </form>
    );
}
