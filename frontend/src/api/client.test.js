import { afterEach, beforeEach, test } from 'node:test';
import assert from 'node:assert/strict';
import { api, listAll } from './client.js';

const originalFetch = globalThis.fetch;
const originalStorage = globalThis.localStorage;
beforeEach(() => {
  const values = new Map([['access', 'old-access'], ['refresh', 'refresh-token']]);
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
});
afterEach(() => { globalThis.fetch = originalFetch; globalThis.localStorage = originalStorage; });

test('field validation errors identify the rejected field', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({contact: {company_email: ['Enter a valid email address.']}}), {status: 400});
  await assert.rejects(api('/employees/'), /contact — company email: Enter a valid email address/);
});

test('concurrent expired requests share one token refresh and retry successfully', async () => {
  let refreshCalls = 0;
  let releaseRefresh;
  const barrier = new Promise((resolve) => { releaseRefresh = resolve; });
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/auth/refresh/')) {
      refreshCalls += 1;
      await barrier;
      return new Response(JSON.stringify({access: 'new-access', refresh: 'new-refresh'}));
    }
    return options.headers.get('Authorization') === 'Bearer new-access'
      ? new Response(JSON.stringify({ok: true}))
      : new Response(JSON.stringify({detail: 'Token expired'}), {status: 401});
  };
  const requests = [api('/employees/'), api('/leave/')];
  await new Promise((resolve) => setTimeout(resolve, 0));
  releaseRefresh();
  assert.deepEqual(await Promise.all(requests), [{ok: true}, {ok: true}]);
  assert.equal(refreshCalls, 1);
  assert.equal(localStorage.getItem('refresh'), 'new-refresh');
});

test('rejected refresh clears the expired session', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({detail: 'Expired session'}), {status: 401});
  await assert.rejects(api('/employees/'), /Expired session/);
  assert.equal(localStorage.getItem('access'), null);
  assert.equal(localStorage.getItem('refresh'), null);
});

test('unreachable backend gives an actionable connection error', async () => {
  globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
  await assert.rejects(api('/employees/'), /local backend is running/);
});

test('authenticated file requests preserve binary content', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.get('Authorization'), 'Bearer old-access');
    return new Response(new Uint8Array([0, 255, 17]), {headers: {'Content-Type': 'application/octet-stream'}});
  };
  const blob = await api('/documents/download/', {responseType: 'blob'});
  assert.deepEqual(new Uint8Array(await blob.arrayBuffer()), new Uint8Array([0, 255, 17]));
});

test('dropdown options include records beyond the first API page', async () => {
  const urls = [];
  globalThis.fetch = async (url) => {
    urls.push(url);
    return new Response(JSON.stringify(url.endsWith('?page=2')
      ? {results: [{id: 'last-position'}], next: null}
      : {results: [{id: 'first-position'}], next: 'http://127.0.0.1:8000/api/organization/options/?page=2'}));
  };
  assert.deepEqual(await listAll('/organization/options/'), [{id: 'first-position'}, {id: 'last-position'}]);
  assert.equal(urls.length, 2);
});

test('pagination does not send tokens to a different host', async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response(JSON.stringify({results: [], next: 'https://other.example/api/options/'}));
  };
  await assert.rejects(listAll('/organization/options/'), /invalid pagination URL/);
  assert.equal(calls, 1);
});
