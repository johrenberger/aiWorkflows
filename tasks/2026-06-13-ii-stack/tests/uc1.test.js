/**
 * UC1 integration test: GET /proxy/pets/:petId/visits
 * Hits the real PetClinic-REST upstream.
 *
 * Uses pet 8 (Samantha in the original seed) which has
 * 2 visits on 2013-01-02 and 2013-01-03. Pet 7 was used
 * by UC2 (POST tests) and has a different visit count
 * now.
 */

const request = require('supertest');
const app = require('../src/server');

describe('UC1: GET /proxy/pets/:petId/visits', () => {
    test('returns all visits for pet 8 when no date range', async () => {
        const res = await request(app).get('/proxy/pets/8/visits');
        expect(res.status).toBe(200);
        expect(res.body.petId).toBe(8);
        expect(res.body.count).toBe(2);
        expect(res.body.visits).toHaveLength(2);
    });

    test('filters by from date (inclusive)', async () => {
        const res = await request(app).get('/proxy/pets/8/visits').query({ from: '2013-01-03' });
        expect(res.status).toBe(200);
        expect(res.body.count).toBe(1);
        expect(res.body.visits[0].date).toBe('2013-01-03');
    });

    test('filters by to date (inclusive)', async () => {
        const res = await request(app).get('/proxy/pets/8/visits').query({ to: '2013-01-02' });
        expect(res.status).toBe(200);
        expect(res.body.count).toBe(1);
        expect(res.body.visits[0].date).toBe('2013-01-02');
    });

    test('filters by from and to date together', async () => {
        const res = await request(app)
            .get('/proxy/pets/8/visits')
            .query({ from: '2013-01-02', to: '2013-01-02' });
        expect(res.status).toBe(200);
        expect(res.body.count).toBe(1);
        expect(res.body.visits[0].date).toBe('2013-01-02');
    });

    test('returns 400 for non-numeric petId', async () => {
        const res = await request(app).get('/proxy/pets/abc/visits');
        expect(res.status).toBe(400);
    });
});
