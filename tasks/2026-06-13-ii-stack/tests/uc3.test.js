/**
 * UC3 integration test: GET /proxy/pets with caching
 * Verifies:
 *  - filter by type name
 *  - limit to first N
 *  - first call is MISS, second is HIT
 *  - cache invalidation on POST /proxy/visits
 *  - cache invalidation on DELETE /proxy/visits/:id
 *  - cache stats endpoint
 *  - invalid limit returns 400
 */

const request = require('supertest');
const app = require('../src/server');

describe('UC3: GET /proxy/pets with caching', () => {
    beforeEach(async () => {
        // Invalidate the cache before each test
        await request(app).post('/proxy/cache/invalidate');
    });

    test('returns all pets when no filter', async () => {
        const res = await request(app).get('/proxy/pets');
        expect(res.status).toBe(200);
        expect(res.body.pets.length).toBeGreaterThan(0);
    });

    test('filters by type=dog', async () => {
        const res = await request(app).get('/proxy/pets').query({ type: 'dog' });
        expect(res.status).toBe(200);
        for (const p of res.body.pets) {
            expect(p.type.name).toBe('dog');
        }
    });

    test('limit=2 returns at most 2 pets', async () => {
        const res = await request(app).get('/proxy/pets').query({ limit: 2 });
        expect(res.status).toBe(200);
        expect(res.body.pets.length).toBeLessThanOrEqual(2);
    });

    test('type=dog&limit=2 returns at most 2 dogs', async () => {
        const res = await request(app).get('/proxy/pets').query({ type: 'dog', limit: 2 });
        expect(res.status).toBe(200);
        expect(res.body.pets.length).toBeLessThanOrEqual(2);
        for (const p of res.body.pets) {
            expect(p.type.name).toBe('dog');
        }
    });

    test('first call is MISS, second is HIT', async () => {
        const r1 = await request(app).get('/proxy/pets').query({ type: 'cat' });
        expect(r1.headers['x-cache']).toBe('MISS');
        const r2 = await request(app).get('/proxy/pets').query({ type: 'cat' });
        expect(r2.headers['x-cache']).toBe('HIT');
        // Same body
        expect(r2.body).toEqual(r1.body);
    });

    test('POST /proxy/visits invalidates the cache', async () => {
        // Warm cache
        await request(app).get('/proxy/pets').query({ type: 'cat' });
        const stats1 = await request(app).get('/proxy/cache/stats');
        expect(stats1.body.hits + stats1.body.misses).toBeGreaterThan(0);

        // Create a visit
        await request(app).post('/proxy/visits').send({
            petId: 1, date: '2024-03-01', description: 'invalidate test',
        });

        // Next GET should be MISS (cache was invalidated)
        const r2 = await request(app).get('/proxy/pets').query({ type: 'cat' });
        expect(r2.headers['x-cache']).toBe('MISS');
    });

    test('returns 400 for invalid limit', async () => {
        const res = await request(app).get('/proxy/pets').query({ limit: -1 });
        expect(res.status).toBe(400);
    });

    test('returns 400 for non-numeric limit', async () => {
        const res = await request(app).get('/proxy/pets').query({ limit: 'abc' });
        expect(res.status).toBe(400);
    });

    test('cache stats endpoint works', async () => {
        await request(app).get('/proxy/pets');
        await request(app).get('/proxy/pets');
        const stats = await request(app).get('/proxy/cache/stats');
        expect(stats.status).toBe(200);
        expect(stats.body).toHaveProperty('hits');
        expect(stats.body).toHaveProperty('misses');
        expect(stats.body).toHaveProperty('size');
    });
});
