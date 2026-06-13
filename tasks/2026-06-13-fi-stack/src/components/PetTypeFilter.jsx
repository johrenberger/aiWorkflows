/**
 * PetTypeFilter — Use case #3 (with frontend-implementation skill)
 *
 * A combobox that lets the user filter pets by type
 * (dog, cat, lizard, snake, bird, hamster).
 *
 * Skill-driven design choices (per react profile + a11y):
 *  - Implements the WAI-ARIA 1.2 combobox pattern:
 *    role="combobox", aria-expanded, aria-controls, aria-activedescendant
 *  - Keyboard navigation: ArrowDown, ArrowUp, Enter, Escape, Home, End
 *  - Debounced server-side filtering (200ms)
 *  - aria-live region announces result count
 *  - Click-outside to close
 *  - Empty state ("No matches")
 *  - Loading state
 *  - Selection is announced to screen readers
 *  - No new dependencies (no downshift, no react-aria)
 */
import React, {
    useEffect,
    useId,
    useRef,
    useState,
    useCallback,
} from 'react';

const PROXY_BASE = import.meta.env.VITE_PROXY_BASE || 'http://localhost:3001';
const DEBOUNCE_MS = 200;

export function PetTypeFilter() {
    const [inputValue, setInputValue] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [activeIndex, setActiveIndex] = useState(-1);
    const [loading, setLoading] = useState(false);
    const [selected, setSelected] = useState(null);
    const inputRef = useRef(null);
    const listRef = useRef(null);
    const comboboxId = useId();
    const listboxId = `${comboboxId}-listbox`;
    const labelId = `${comboboxId}-label`;
    const statusId = `${comboboxId}-status`;

    // Debounced fetch
    useEffect(() => {
        if (!inputValue.trim()) {
            setSuggestions([]);
            return;
        }
        setLoading(true);
        const handle = setTimeout(async () => {
            try {
                const r = await fetch(
                    `${PROXY_BASE}/proxy/pets?type=${encodeURIComponent(
                        inputValue.trim().toLowerCase()
                    )}&limit=10`
                );
                if (!r.ok) {
                    setSuggestions([]);
                } else {
                    const data = await r.json();
                    setSuggestions(data.pets || []);
                }
            } catch {
                setSuggestions([]);
            } finally {
                setLoading(false);
            }
        }, DEBOUNCE_MS);
        return () => clearTimeout(handle);
    }, [inputValue]);

    // Click-outside to close
    useEffect(() => {
        if (!isOpen) return undefined;
        const onClick = (e) => {
            if (
                inputRef.current &&
                !inputRef.current.contains(e.target) &&
                listRef.current &&
                !listRef.current.contains(e.target)
            ) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', onClick);
        return () => document.removeEventListener('mousedown', onClick);
    }, [isOpen]);

    const onKeyDown = useCallback(
        (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setIsOpen(true);
                setActiveIndex((i) =>
                    i < suggestions.length - 1 ? i + 1 : 0
                );
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setIsOpen(true);
                setActiveIndex((i) =>
                    i > 0 ? i - 1 : suggestions.length - 1
                );
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeIndex >= 0 && suggestions[activeIndex]) {
                    selectSuggestion(suggestions[activeIndex]);
                }
            } else if (e.key === 'Escape') {
                setIsOpen(false);
            } else if (e.key === 'Home') {
                e.preventDefault();
                setActiveIndex(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                setActiveIndex(suggestions.length - 1);
            }
        },
        [activeIndex, suggestions]
    );

    const selectSuggestion = (pet) => {
        setSelected(pet);
        setInputValue(pet.name);
        setIsOpen(false);
        setActiveIndex(-1);
    };

    return (
        <div>
            <label id={labelId} htmlFor={`${comboboxId}-input`}>
                Find a pet by name
            </label>
            <div
                style={{ position: 'relative' }}
                ref={inputRef}
            >
                <input
                    id={`${comboboxId}-input`}
                    type="text"
                    role="combobox"
                    aria-expanded={isOpen}
                    aria-controls={listboxId}
                    aria-autocomplete="list"
                    aria-activedescendant={
                        activeIndex >= 0
                            ? `${comboboxId}-option-${activeIndex}`
                            : undefined
                    }
                    aria-labelledby={labelId}
                    value={inputValue}
                    onChange={(e) => {
                        setInputValue(e.target.value);
                        setIsOpen(true);
                        setActiveIndex(-1);
                    }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={onKeyDown}
                    placeholder="Start typing a pet name"
                    style={{ marginTop: '0.5rem' }}
                />
                {isOpen && inputValue.trim() && (
                    <ul
                        ref={listRef}
                        id={listboxId}
                        role="listbox"
                        aria-labelledby={labelId}
                        style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            margin: 0,
                            padding: 0,
                            listStyle: 'none',
                            background: 'white',
                            border: '1px solid var(--color-border)',
                            borderRadius: 'var(--radius)',
                            maxHeight: '200px',
                            overflowY: 'auto',
                            zIndex: 10,
                        }}
                    >
                        {loading && (
                            <li style={{ padding: '0.5rem' }} role="option" aria-disabled="true">
                                Loading…
                            </li>
                        )}
                        {!loading && suggestions.length === 0 && (
                            <li style={{ padding: '0.5rem' }} role="option" aria-disabled="true">
                                No matches
                            </li>
                        )}
                        {!loading &&
                            suggestions.map((pet, i) => (
                                <li
                                    key={pet.id}
                                    id={`${comboboxId}-option-${i}`}
                                    role="option"
                                    aria-selected={i === activeIndex}
                                    onMouseDown={(e) => {
                                        // mousedown so the input doesn't lose focus first
                                        e.preventDefault();
                                        selectSuggestion(pet);
                                    }}
                                    onMouseEnter={() => setActiveIndex(i)}
                                    style={{
                                        padding: '0.5rem',
                                        background:
                                            i === activeIndex
                                                ? 'var(--color-accent)'
                                                : 'transparent',
                                        color:
                                            i === activeIndex ? 'white' : 'inherit',
                                        cursor: 'pointer',
                                    }}
                                >
                                    {pet.name} ({pet.type?.name})
                                </li>
                            ))}
                    </ul>
                )}
            </div>
            <p
                id={statusId}
                aria-live="polite"
                style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--color-muted)' }}
            >
                {selected
                    ? `Selected: ${selected.name}`
                    : loading
                    ? 'Searching…'
                    : inputValue && suggestions.length > 0
                    ? `${suggestions.length} result${suggestions.length === 1 ? '' : 's'}`
                    : ''}
            </p>
        </div>
    );
}
