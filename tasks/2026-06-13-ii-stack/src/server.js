/**
 * PetClinic Proxy — UC2 (with integration-implementation skill)
 *
 * POST /proxy/visits — creates a new visit via the
 * downstream PetClinic-REST service, with:
 * - explicit timeout (5s)
 * - bounded retry with exponential backoff for 5xx / network errors
 * - no retry for 4xx (client error)
 * - structured error responses with correlation id
 * - logging without secrets
 * - idempotency key (header propagation) for POST retry safety
 *
 * The upstream is a local development instance of
 * johrenberger/spring-petclinic-rest (a fork, not a real
 * production endpoint) — calling it from tests is allowed
 * per the rest-api profile ("Do not call real production
 * endpoints" — a local dev upstream is not a production
 * endpoint).
 */

const express = require('express');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
app.use(express.json());

const DOWNSTREAM_BASE = process.env.DOWNSTREAM_BASE
    || 'http://localhost:9966/petclinic/api';
const DEFAULT_TIMEOUT_MS = parseInt(process.env.DOWNSTREAM_TIMEOUT_MS || '5000', 10);
const MAX_RETRIES = parseInt(process.env.DOWNSTREAM_MAX_RETRIES || '2', 10);

// --- Logging (no secrets; redacts petId, description, id) ---
function logEvent(level, event, fields) {
    // Redact: never log description (free text may contain PII)
    // Always log: correlation id, event name, status, attempt
    const safe = {
        ts: new Date().toISOString(),
        level,
        event,
        correlationId: fields?.correlationId,
        status: fields?.status,
        attempt: fields?.attempt,
        latencyMs: fields?.latencyMs,
    };
    console.log(JSON.stringify(safe));
}

// --- Retry classification ---
function isRetryable(err) {
    if (!err.response) {
        // network error / timeout — retryable
        return true;
    }
    const s = err.response.status;
    return s >= 500 || s === 429;
}

// --- Bounded retry with exponential backoff ---
async function callWithRetry(method, url, options = {}, correlationId) {
    let lastErr = null;
    for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
        const start = Date.now();
        try {
            const res = await axios.request({
                method,
                url,
                ...options,
                timeout: DEFAULT_TIMEOUT_MS,
                headers: {
                    ...(options.headers || {}),
                    'X-Correlation-Id': correlationId,
                },
            });
            logEvent('info', 'downstream.ok', {
                correlationId,
                status: res.status,
                attempt,
                latencyMs: Date.now() - start,
            });
            return res;
        } catch (err) {
            lastErr = err;
            const retryable = isRetryable(err);
            logEvent('warn', 'downstream.err', {
                correlationId,
                status: err.response?.status,
                attempt,
                latencyMs: Date.now() - start,
            });
            if (!retryable || attempt > MAX_RETRIES) {
                throw err;
            }
            // Exponential backoff: 100ms, 200ms, 400ms, ...
            const backoff = 100 * Math.pow(2, attempt - 1);
            await new Promise((r) => setTimeout(r, backoff));
        }
    }
    throw lastErr;
}

// --- Correlation id middleware ---
app.use((req, res, next) => {
    const incoming = req.header('X-Correlation-Id');
    const correlationId = incoming || crypto.randomUUID();
    res.setHeader('X-Correlation-Id', correlationId);
    req.correlationId = correlationId;
    next();
});

// --- Routes ---

// UC1 (carried forward from baseline): GET /proxy/pets/:petId/visits
app.get('/proxy/pets/:petId/visits', async (req, res) => {
    const petId = parseInt(req.params.petId, 10);
    if (isNaN(petId) || petId <= 0) {
        return res.status(400).json({ error: 'petId must be a positive integer' });
    }
    const { from, to } = req.query;
    try {
        const response = await callWithRetry(
            'GET',
            `${DOWNSTREAM_BASE}/pets/${petId}/visits`,
            {},
            req.correlationId,
        );
        let visits = response.data || [];
        if (from) {
            visits = visits.filter((v) => v.date >= from);
        }
        if (to) {
            visits = visits.filter((v) => v.date <= to);
        }
        res.json({
            petId,
            from: from || null,
            to: to || null,
            count: visits.length,
            visits,
        });
    } catch (err) {
        const status = err.response?.status || 502;
        res.status(status).json({
            error: 'upstream error',
            correlationId: req.correlationId,
        });
    }
});

// UC2: POST /proxy/visits with retry, timeout, error classification
app.post('/proxy/visits', async (req, res) => {
    const { petId, date, description } = req.body || {};
    // Validation
    if (typeof petId !== 'number' || petId <= 0) {
        return res.status(400).json({
            error: 'petId must be a positive integer',
            correlationId: req.correlationId,
        });
    }
    if (!date || typeof date !== 'string') {
        return res.status(400).json({
            error: 'date is required (YYYY-MM-DD)',
            correlationId: req.correlationId,
        });
    }
    if (!description || typeof description !== 'string') {
        return res.status(400).json({
            error: 'description is required',
            correlationId: req.correlationId,
        });
    }
    // Idempotency key: if the client provided one, pass it through
    // so retries don't create duplicate visits.
    const idempotencyKey = req.header('Idempotency-Key');
    const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {};
    try {
        const response = await callWithRetry(
            'POST',
            `${DOWNSTREAM_BASE}/visits`,
            {
                headers: { ...headers, 'Content-Type': 'application/json' },
                data: { petId, date, description },
            },
            req.correlationId,
        );
        // Invalidate pet list cache: a new visit changes
        // the pet's visit count, which a downstream caller
        // might want to see fresh.
        petListCache.invalidate();
        res.status(response.status).json(response.data);
    } catch (err) {
        const status = err.response?.status || 502;
        res.status(status).json({
            error: 'upstream error',
            detail: err.response?.data || err.message,
            correlationId: req.correlationId,
        });
    }
});

// Health check
app.get('/proxy/health', (req, res) => {
    res.json({ status: 'ok', downstream: DOWNSTREAM_BASE });
});

// UC3: DELETE /proxy/visits/:id — soft-deletes a visit and
// invalidates the pet list cache.
app.delete('/proxy/visits/:id', async (req, res) => {
    const visitId = parseInt(req.params.id, 10);
    if (isNaN(visitId) || visitId <= 0) {
        return res.status(400).json({
            error: 'visitId must be a positive integer',
            correlationId: req.correlationId,
        });
    }
    try {
        await callWithRetry(
            'DELETE',
            `${DOWNSTREAM_BASE}/visits/${visitId}`,
            {},
            req.correlationId,
        );
        petListCache.invalidate();
        res.status(204).send();
    } catch (err) {
        const status = err.response?.status || 502;
        res.status(status).json({
            error: 'upstream error',
            correlationId: req.correlationId,
        });
    }
});

// --- UC3: In-memory LRU cache for pet type lists ---
//
// GET /proxy/pets?type=dog&limit=10
//
// Returns a list of pets, optionally filtered by type name,
// limited to the first N results. Results are cached in an
// LRU map keyed by (type, limit) and TTL=10s.
//
// The cache is invalidated:
//  - on TTL expiry (10s)
//  - on POST /proxy/visits (any visit creation may change
//    the pet list indirectly via ownerId relationships; we
//    invalidate to be safe)
//  - on DELETE /proxy/visits/:id (soft-delete of a visit)
//
// This is a deliberately small, in-process cache. A
// production system would use Redis or a CDN.

const CACHE_TTL_MS = parseInt(process.env.CACHE_TTL_MS || '10000', 10);
const CACHE_MAX_ENTRIES = parseInt(process.env.CACHE_MAX_ENTRIES || '128', 10);

class LruTtlCache {
    constructor(maxEntries, ttlMs) {
        this.maxEntries = maxEntries;
        this.ttlMs = ttlMs;
        this.map = new Map();
        this.stats = { hits: 0, misses: 0, evictions: 0, invalidations: 0 };
    }
    get(key) {
        const entry = this.map.get(key);
        if (!entry) {
            this.stats.misses++;
            return undefined;
        }
        if (Date.now() - entry.at > this.ttlMs) {
            this.map.delete(key);
            this.stats.evictions++;
            this.stats.misses++;
            return undefined;
        }
        // LRU: re-insert to bump recency
        this.map.delete(key);
        this.map.set(key, entry);
        this.stats.hits++;
        return entry.value;
    }
    set(key, value) {
        if (this.map.has(key)) this.map.delete(key);
        this.map.set(key, { at: Date.now(), value });
        // Evict oldest if over capacity
        while (this.map.size > this.maxEntries) {
            const oldest = this.map.keys().next().value;
            this.map.delete(oldest);
            this.stats.evictions++;
        }
    }
    invalidate() {
        this.map.clear();
        this.stats.invalidations++;
    }
    stats_() {
        return { ...this.stats, size: this.map.size };
    }
}

const petListCache = new LruTtlCache(CACHE_MAX_ENTRIES, CACHE_TTL_MS);

app.get('/proxy/pets', async (req, res) => {
    const { type, limit } = req.query;
    const limitN = limit ? parseInt(limit, 10) : null;
    if (limit !== undefined && (isNaN(limitN) || limitN <= 0)) {
        return res.status(400).json({ error: 'limit must be a positive integer' });
    }
    const cacheKey = `pets:type=${type || ''}:limit=${limitN || ''}`;
    const cached = petListCache.get(cacheKey);
    if (cached) {
        res.setHeader('X-Cache', 'HIT');
        return res.json(cached);
    }
    try {
        const response = await callWithRetry(
            'GET',
            `${DOWNSTREAM_BASE}/pets`,
            {},
            req.correlationId,
        );
        let pets = response.data || [];
        if (type) {
            const t = String(type).toLowerCase();
            pets = pets.filter((p) => p.type?.name?.toLowerCase() === t);
        }
        if (limitN) {
            pets = pets.slice(0, limitN);
        }
        const payload = {
            type: type || null,
            limit: limitN,
            count: pets.length,
            pets,
        };
        petListCache.set(cacheKey, payload);
        res.setHeader('X-Cache', 'MISS');
        res.json(payload);
    } catch (err) {
        const status = err.response?.status || 502;
        res.status(status).json({
            error: 'upstream error',
            correlationId: req.correlationId,
        });
    }
});

// Cache stats endpoint (operational, for monitoring)
app.get('/proxy/cache/stats', (req, res) => {
    res.json(petListCache.stats_());
});

// Invalidate cache explicitly (for ops, future work)
app.post('/proxy/cache/invalidate', (req, res) => {
    petListCache.invalidate();
    res.json({ invalidated: true });
});

if (require.main === module) {
    const port = process.env.PORT || 3001;
    app.listen(port, () => {
        console.log(`PetClinic proxy listening on port ${port}`);
    });
}

module.exports = app;
module.exports.callWithRetry = callWithRetry;
module.exports.isRetryable = isRetryable;
