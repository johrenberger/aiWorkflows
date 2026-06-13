/**
 * PetVisitList — Use case #1 (no skill baseline)
 *
 * Fetches /proxy/pets/:petId/visits and renders a table.
 * Renders a loading state, an error state, or the table.
 *
 * This is the no-skill baseline. The version is intentionally
 * minimal: a simple fetch + render with no accessibility
 * considerations beyond `<table>`.
 */
import React, { useEffect, useState } from 'react';

const PROXY_BASE = import.meta.env.VITE_PROXY_BASE || 'http://localhost:3001';

export function PetVisitList({ petId }) {
    const [visits, setVisits] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!petId || petId <= 0) {
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        fetch(`${PROXY_BASE}/proxy/pets/${petId}/visits`)
            .then((r) => {
                if (!r.ok) {
                    throw new Error(`HTTP ${r.status}`);
                }
                return r.json();
            })
            .then((data) => {
                setVisits(data.visits || []);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, [petId]);

    if (loading) return <p>Loading...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!visits || visits.length === 0) return <p>No visits for this pet.</p>;

    return (
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {visits.map((v) => (
                    <tr key={v.id}>
                        <td>{v.date}</td>
                        <td>{v.description}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}
