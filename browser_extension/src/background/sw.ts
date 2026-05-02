// Background service worker: dispatch table + side-effects.
//
//  - Routes messages from side panel and content script to handlers.
//  - Owns the auth flow (chrome.identity.launchWebAuthFlow → token rotation).
//  - Subscribes to chrome.tabs.onUpdated; broadcasts URL changes to content
//    scripts and updates the toolbar icon badge based on auth + duplicate state.

import { api, ApiError } from "@shared/api-client";
import { normalizeUrl } from "@shared/normalize-url";
import { auth, baseUrl as baseUrlStore, lastProject, urlCache } from "@shared/storage";
import type {
  AuthState,
  CaptureMsgResponse,
  CaptureRequest,
  CheckResult,
  CheckUrlRequest,
  CheckUrlResponse,
  ClearAuthRequest,
  ClearAuthResponse,
  ExtensionMessage,
  GetAuthStateRequest,
  GetAuthStateResponse,
  GetProjectsRequest,
  GetProjectsResponse,
  InitiateAuthRequest,
  InitiateAuthResponse,
  ScreenshotRequest,
  ScreenshotResponse,
  SuggestMsgResponse,
  SuggestRequest,
} from "@shared/types";

// --- Side panel ------------------------------------------------------------

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((err) => console.error("[crane] sidePanel.setPanelBehavior failed", err));
});

// --- Default base URL ------------------------------------------------------
//
// The side panel `Connect` button opens
// `${baseUrl}/auth/extension-link/?ext_id=<id>`. The user picks the base URL
// from the Connect screen on first install; it's persisted to
// `chrome.storage.local["craneBaseUrl"]` (separate from auth, so Disconnect
// doesn't wipe it).
export const DEFAULT_BASE_URL = "http://localhost:8000";

async function resolveBaseUrl(): Promise<string> {
  return (await baseUrlStore.load()) ?? (await auth.load())?.baseUrl ?? DEFAULT_BASE_URL;
}

// --- Auth flow -------------------------------------------------------------

async function handleInitiateAuth(msg: InitiateAuthRequest): Promise<InitiateAuthResponse> {
  if (msg.baseUrl) await baseUrlStore.save(msg.baseUrl);
  const baseUrl = await resolveBaseUrl();
  const extId = chrome.runtime.id;
  const linkUrl = `${baseUrl}/auth/extension-link/?ext_id=${encodeURIComponent(extId)}`;

  let redirectUrl: string | undefined;
  try {
    redirectUrl = await chrome.identity.launchWebAuthFlow({
      url: linkUrl,
      interactive: true,
    });
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
  if (!redirectUrl) {
    return { ok: false, error: "Auth was cancelled" };
  }

  let parsed: URL;
  try {
    parsed = new URL(redirectUrl);
  } catch {
    return { ok: false, error: "Auth redirect URL was malformed" };
  }
  const token = parsed.searchParams.get("token");
  const email = parsed.searchParams.get("email");
  if (!token || !email) {
    return { ok: false, error: "Auth redirect was missing token or email" };
  }

  const state: AuthState = { token, email, baseUrl };
  await auth.save(state);
  await urlCache.clear();
  // Broadcast to any open side panel; content scripts ignore.
  chrome.runtime.sendMessage({ type: "AUTH_UPDATED", auth: state }).catch(noop);
  await refreshActiveTabBadge();
  return { ok: true, data: state };
}

async function handleClearAuth(_msg: ClearAuthRequest): Promise<ClearAuthResponse> {
  await auth.clear();
  await urlCache.clear();
  chrome.runtime.sendMessage({ type: "AUTH_CLEARED" }).catch(noop);
  await refreshActiveTabBadge();
  return { ok: true, data: null };
}

async function handleGetAuthState(_msg: GetAuthStateRequest): Promise<GetAuthStateResponse> {
  return { ok: true, data: await auth.load() };
}

// --- API passthroughs ------------------------------------------------------

async function handleGetProjects(_msg: GetProjectsRequest): Promise<GetProjectsResponse> {
  try {
    return { ok: true, data: await api.getProjects() };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

async function handleCheckUrl(msg: CheckUrlRequest): Promise<CheckUrlResponse> {
  const normalized = normalizeUrl(msg.url);
  if (!normalized) {
    return { ok: true, data: { duplicate: false, record_id: null } };
  }
  const cached = await urlCache.lookup(normalized, msg.projectId);
  if (cached) return { ok: true, data: cached };
  try {
    const result = await api.checkUrl(msg.url, msg.projectId);
    await urlCache.write(normalized, msg.projectId, result);
    return { ok: true, data: result };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

async function handleSuggest(msg: SuggestRequest): Promise<SuggestMsgResponse> {
  try {
    return { ok: true, data: await api.getSuggestions(msg.projectId) };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

async function handleCapture(msg: CaptureRequest): Promise<CaptureMsgResponse> {
  try {
    const result = await api.capture(msg.payload);
    // Invalidate cache for the captured URL so the badge flips to amber.
    const normalized = normalizeUrl(msg.payload.url);
    if (normalized) await urlCache.clear();
    return { ok: true, data: result };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

async function handleScreenshot(_msg: ScreenshotRequest): Promise<ScreenshotResponse> {
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab({ format: "png" });
    return { ok: true, data: dataUrl };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

// --- Dispatch --------------------------------------------------------------

type Handler<M extends ExtensionMessage, R> = (msg: M) => Promise<R>;

const handlers: { [K in ExtensionMessage["type"]]?: Handler<any, any> } = {
  INITIATE_AUTH: handleInitiateAuth,
  CLEAR_AUTH: handleClearAuth,
  GET_AUTH_STATE: handleGetAuthState,
  GET_PROJECTS: handleGetProjects,
  CHECK_URL: handleCheckUrl,
  CAPTURE: handleCapture,
  GET_SUGGESTIONS: handleSuggest,
  TAKE_SCREENSHOT: handleScreenshot,
};

chrome.runtime.onMessage.addListener((rawMsg, _sender, sendResponse) => {
  const msg = rawMsg as ExtensionMessage;
  const handler = handlers[msg.type as keyof typeof handlers];
  if (!handler) {
    // Broadcasts (PAGE_URL_CHANGED, AUTH_*) flow through here too; ignore them.
    return false;
  }
  handler(msg).then(sendResponse).catch((err) => {
    sendResponse({ ok: false, error: errorMessage(err) });
  });
  return true; // keep the channel open for the async response
});

// --- Tab tracking + badge --------------------------------------------------

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (!tab.url) return;
  // Status === "loading" with a url change covers SPA history-state pushes.
  if (changeInfo.url || changeInfo.status === "complete") {
    if (changeInfo.url) {
      chrome.tabs
        .sendMessage(tabId, { type: "PAGE_URL_CHANGED", url: tab.url })
        .catch(noop);
    }
    if (tab.active) {
      await refreshBadgeForTab(tab);
    }
  }
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    await refreshBadgeForTab(tab);
  } catch {
    /* tab gone */
  }
});

async function refreshActiveTabBadge(): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) await refreshBadgeForTab(tab);
}

async function refreshBadgeForTab(tab: chrome.tabs.Tab): Promise<void> {
  const tabId = tab.id;
  if (typeof tabId !== "number") return;

  const a = await auth.load();
  if (!a) {
    await setBadge(tabId, { text: "", color: "#94a3b8", title: "Crane — not connected" });
    return;
  }
  const projectId = await lastProject.load();
  const url = tab.url ?? "";
  if (!projectId || !url || !/^https?:/i.test(url)) {
    await setBadge(tabId, { text: "", color: "#22c55e", title: "Crane — connected" });
    return;
  }

  const normalized = normalizeUrl(url);
  if (!normalized) {
    await setBadge(tabId, { text: "", color: "#22c55e", title: "Crane — connected" });
    return;
  }

  let result: CheckResult | null = await urlCache.lookup(normalized, projectId);
  if (!result) {
    try {
      result = await api.checkUrl(url, projectId);
      await urlCache.write(normalized, projectId, result);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      const text = status === 401 ? "!" : "?";
      const color = status === 401 ? "#ef4444" : "#94a3b8";
      await setBadge(tabId, {
        text,
        color,
        title: `Crane — ${errorMessage(err)}`,
      });
      return;
    }
  }
  if (result.duplicate) {
    await setBadge(tabId, {
      text: "!",
      color: "#f59e0b",
      title: `Crane — already captured (${result.record_id})`,
    });
  } else {
    await setBadge(tabId, { text: "", color: "#22c55e", title: "Crane — fresh" });
  }
}

async function setBadge(
  tabId: number,
  opts: { text: string; color: string; title: string },
): Promise<void> {
  await Promise.all([
    chrome.action.setBadgeText({ tabId, text: opts.text }),
    chrome.action.setBadgeBackgroundColor({ tabId, color: opts.color }),
    chrome.action.setTitle({ tabId, title: opts.title }),
  ]).catch(noop);
}

// --- Utilities -------------------------------------------------------------

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "Unknown error";
}

function noop(): void {
  /* swallow */
}
