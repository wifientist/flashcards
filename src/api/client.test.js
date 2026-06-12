import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, apiFetch, ApiError } from './client';

function res(status, data) {
  return {
    status,
    ok: status >= 200 && status < 300,
    text: async () => (data === undefined ? '' : JSON.stringify(data)),
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(async () => {
  // Let the client's internal refresh-promise reset (setTimeout 0) settle.
  await new Promise((r) => setTimeout(r, 0));
});

describe('apiFetch', () => {
  it('returns parsed JSON on success', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(res(200, { hello: 'world' }));
    await expect(api.get('/api/cards')).resolves.toEqual({ hello: 'world' });
  });

  it('throws ApiError with status + detail on failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(res(400, { detail: 'bad' }));
    await expect(api.get('/api/cards')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'bad',
    });
  });

  it('refreshes once and replays the request on 401', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(res(401, { detail: 'expired' })) // initial
      .mockResolvedValueOnce(res(200, {})) // refresh succeeds
      .mockResolvedValueOnce(res(200, { data: 1 })); // replay
    globalThis.fetch = fetch;

    await expect(api.get('/api/cards')).resolves.toEqual({ data: 1 });
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls[1][0]).toBe('/api/auth/refresh');
  });

  it('coalesces concurrent 401s into a single refresh', async () => {
    let refreshCalls = 0;
    const seen = {};
    globalThis.fetch = vi.fn(async (path) => {
      if (path === '/api/auth/refresh') {
        refreshCalls += 1;
        return res(200, {});
      }
      seen[path] = (seen[path] || 0) + 1;
      return seen[path] === 1 ? res(401, {}) : res(200, { ok: path });
    });

    await Promise.all([api.get('/api/cards'), api.get('/api/decks')]);
    expect(refreshCalls).toBe(1);
  });

  it('emits auth:logout and throws when refresh fails', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(res(401, {})) // initial
      .mockResolvedValueOnce(res(401, {})); // refresh also 401
    const onLogout = vi.fn();
    window.addEventListener('auth:logout', onLogout);

    await expect(api.get('/api/cards')).rejects.toBeInstanceOf(ApiError);
    expect(onLogout).toHaveBeenCalled();
    window.removeEventListener('auth:logout', onLogout);
  });

  it('does not attempt refresh for auth endpoints', async () => {
    const fetch = vi.fn().mockResolvedValue(res(401, { detail: 'nope' }));
    globalThis.fetch = fetch;
    await expect(apiFetch('/api/auth/login', { method: 'POST' })).rejects.toBeInstanceOf(ApiError);
    expect(fetch).toHaveBeenCalledTimes(1); // no refresh/replay
  });
});
