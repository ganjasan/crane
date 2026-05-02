// Typed wrappers over chrome.storage.local. All persistent state for the
// extension lives here:
//   - craneAuth        : AuthState | null  (token, email, baseUrl)
//   - craneLastProject : string  | null    (project id of last successful capture)
//   - craneUrlCache    : Record<normalizedUrl, { result, ts }>
//
// Keys are stable strings — never inline them elsewhere; import the helpers.

import type { AuthState, CheckResult } from "./types";

const KEY_AUTH = "craneAuth";
const KEY_BASE_URL = "craneBaseUrl";
const KEY_LAST_PROJECT = "craneLastProject";
const KEY_URL_CACHE = "craneUrlCache";

const URL_CACHE_TTL_MS = 5 * 60 * 1000;
const URL_CACHE_MAX_ENTRIES = 200;

type UrlCacheEntry = { result: CheckResult; ts: number; projectId: string };
type UrlCache = Record<string, UrlCacheEntry>;

async function get<T>(key: string): Promise<T | null> {
  const items = await chrome.storage.local.get(key);
  return (items[key] as T | undefined) ?? null;
}

async function set<T>(key: string, value: T): Promise<void> {
  await chrome.storage.local.set({ [key]: value });
}

async function remove(key: string): Promise<void> {
  await chrome.storage.local.remove(key);
}

// --- Auth -----------------------------------------------------------------

export const auth = {
  async load(): Promise<AuthState | null> {
    return get<AuthState>(KEY_AUTH);
  },
  async save(state: AuthState): Promise<void> {
    await set(KEY_AUTH, state);
  },
  async clear(): Promise<void> {
    await remove(KEY_AUTH);
  },
};

// --- Base URL (persists separately from auth so we don't lose it on Disconnect)

export const baseUrl = {
  async load(): Promise<string | null> {
    return get<string>(KEY_BASE_URL);
  },
  async save(value: string): Promise<void> {
    await set(KEY_BASE_URL, value);
  },
};

// --- Last-used project ----------------------------------------------------

export const lastProject = {
  async load(): Promise<string | null> {
    return get<string>(KEY_LAST_PROJECT);
  },
  async save(projectId: string): Promise<void> {
    await set(KEY_LAST_PROJECT, projectId);
  },
};

// --- URL cache ------------------------------------------------------------

export const urlCache = {
  async load(): Promise<UrlCache> {
    return (await get<UrlCache>(KEY_URL_CACHE)) ?? {};
  },
  async lookup(
    normalizedUrl: string,
    projectId: string,
  ): Promise<CheckResult | null> {
    const cache = await urlCache.load();
    const entry = cache[normalizedUrl];
    if (!entry) return null;
    if (entry.projectId !== projectId) return null;
    if (Date.now() - entry.ts > URL_CACHE_TTL_MS) return null;
    return entry.result;
  },
  async write(
    normalizedUrl: string,
    projectId: string,
    result: CheckResult,
  ): Promise<void> {
    const cache = await urlCache.load();
    cache[normalizedUrl] = { result, ts: Date.now(), projectId };
    // Trim oldest entries when over budget.
    const keys = Object.keys(cache);
    if (keys.length > URL_CACHE_MAX_ENTRIES) {
      const sorted = keys
        .map((k) => [k, cache[k]!.ts] as const)
        .sort((a, b) => a[1] - b[1]);
      const toDrop = sorted.slice(0, keys.length - URL_CACHE_MAX_ENTRIES);
      for (const [k] of toDrop) delete cache[k];
    }
    await set(KEY_URL_CACHE, cache);
  },
  async clear(): Promise<void> {
    await remove(KEY_URL_CACHE);
  },
};
