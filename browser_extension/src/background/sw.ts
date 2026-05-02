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
  DetectLanguageRequest,
  DetectLanguageResponse,
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
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url || !/^https?:/i.test(tab.url)) {
      return { ok: false, error: "Cannot screenshot this page" };
    }
    const dataUrl = await captureFullPage(tab.id, tab.windowId);
    return { ok: true, data: dataUrl };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

// Inspect the active tab and return a best-guess ISO 639-1 language code.
// First reads <html lang>; falls back to chrome.i18n on a body-text sample.
async function handleDetectLanguage(
  _msg: DetectLanguageRequest,
): Promise<DetectLanguageResponse> {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url || !/^https?:/i.test(tab.url)) {
      return { ok: true, data: null };
    }
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractLanguageHints,
    });
    const hint = results[0]?.result;
    if (!hint) return { ok: true, data: null };

    if (hint.htmlLang) return { ok: true, data: hint.htmlLang };

    if (hint.sampleText && chrome.i18n?.detectLanguage) {
      const detected = await chrome.i18n.detectLanguage(hint.sampleText);
      const top = detected?.languages?.[0];
      if (top && top.language && top.percentage >= 30) {
        return { ok: true, data: top.language };
      }
    }
    return { ok: true, data: null };
  } catch (err) {
    return { ok: false, error: errorMessage(err) };
  }
}

// Injected: read <html lang> and a sample of visible body text.
function extractLanguageHints(): { htmlLang: string; sampleText: string } {
  const rawLang = (document.documentElement.getAttribute("lang") || "").trim().toLowerCase();
  const match = /^[a-z]{2,3}/.exec(rawLang);
  const htmlLang = match ? match[0] : "";
  const text = (document.body?.innerText ?? "").replace(/\s+/g, " ").trim().slice(0, 4000);
  return { htmlLang, sampleText: text };
}

// --- Full-page screenshot --------------------------------------------------
//
// Algorithm: inject a preparation script (records page metrics, sets
// position:fixed/sticky elements to position:absolute so they don't appear
// in every slice, disables smooth-scroll). Scroll-and-capture in a loop,
// pacing 600ms between captures to stay under chrome.tabs.captureVisibleTab's
// ~2/sec quota. After all slices, restore page state. Stitch onto an
// OffscreenCanvas and return the encoded data URL.

type PrepareResult = {
  totalHeight: number;
  viewportHeight: number;
  viewportWidth: number;
  dpr: number;
  originalScroll: number;
};

async function captureFullPage(tabId: number, windowId: number): Promise<string> {
  const prepResults = await chrome.scripting.executeScript({
    target: { tabId },
    func: prepareForCapture,
  });
  const meta = prepResults[0]?.result;
  if (!meta) throw new Error("Failed to read page dimensions");

  const totalSlices = Math.max(
    1,
    Math.min(
      40,
      Math.ceil(Math.max(meta.totalHeight, meta.viewportHeight) / meta.viewportHeight),
    ),
  );

  // Tell the page that capture is starting so it can show a banner.
  await chrome.scripting
    .executeScript({ target: { tabId }, func: injectOverlay, args: [totalSlices] })
    .catch(noop);
  // And tell the side panel.
  broadcastProgress(0, totalSlices);

  const slices: { dataUrl: string; y: number }[] = [];
  try {
    const step = meta.viewportHeight;
    const maxScroll = Math.max(0, meta.totalHeight - meta.viewportHeight);
    let y = 0;
    let captures = 0;
    // Hard cap to avoid runaway loops on infinite-scroll pages.
    const MAX_SLICES = 40;
    while (captures < MAX_SLICES) {
      const targetY = Math.min(y, maxScroll);
      // Scroll, hide overlay, wait paint — all in one round-trip to the page.
      await chrome.scripting.executeScript({
        target: { tabId },
        func: scrollAndHideOverlay,
        args: [targetY],
      });
      // Throttle for captureVisibleTab quota.
      if (captures > 0) await sleep(600);
      const dataUrl = await chrome.tabs.captureVisibleTab(windowId, { format: "png" });
      slices.push({ dataUrl, y: targetY });
      captures++;
      // Show overlay back with updated progress text.
      await chrome.scripting
        .executeScript({
          target: { tabId },
          func: showOverlayWithProgress,
          args: [captures, totalSlices],
        })
        .catch(noop);
      broadcastProgress(captures, totalSlices);
      if (y >= maxScroll) break;
      y += step;
    }
  } finally {
    await chrome.scripting
      .executeScript({
        target: { tabId },
        func: restoreAfterCapture,
        args: [meta.originalScroll],
      })
      .catch(noop);
    broadcastProgress(null, null);
  }

  return stitchSlices(slices, meta.totalHeight, meta.dpr);
}

function broadcastProgress(current: number | null, total: number | null): void {
  // Side panel listens for this and updates its busy UI.
  chrome.runtime
    .sendMessage({ type: "CAPTURE_PROGRESS", current, total })
    .catch(noop);
}

// Functions below are injected into the page via chrome.scripting.executeScript.
// They run in the page's isolated world; they MUST be self-contained (no closure
// references) because esbuild serializes them by `.toString()`.

function prepareForCapture(): PrepareResult {
  const dpr = window.devicePixelRatio || 1;
  const totalHeight = Math.max(
    document.body.scrollHeight,
    document.documentElement.scrollHeight,
    document.body.offsetHeight,
    document.documentElement.offsetHeight,
  );
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  const originalScroll = window.scrollY;

  // Neutralize fixed/sticky positioning so headers don't appear in every slice.
  const els = document.querySelectorAll<HTMLElement>("*");
  for (const el of Array.from(els)) {
    const cs = getComputedStyle(el);
    if (cs.position === "fixed" || cs.position === "sticky") {
      el.dataset["craneOrigPos"] = el.style.position;
      el.style.setProperty("position", "absolute", "important");
    }
  }
  // Force instant scrolling between slices.
  document.documentElement.dataset["craneOrigScroll"] = document.documentElement.style.scrollBehavior;
  document.documentElement.style.scrollBehavior = "auto";

  return { totalHeight, viewportHeight, viewportWidth, dpr, originalScroll };
}

async function scrollAndHideOverlay(y: number): Promise<void> {
  // Hide the in-page banner so it doesn't appear in this slice.
  const overlay = document.getElementById("crane-capture-overlay");
  if (overlay) overlay.style.visibility = "hidden";
  window.scrollTo(0, y);
  await new Promise<void>((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
  );
}

function showOverlayWithProgress(current: number, total: number): void {
  const overlay = document.getElementById("crane-capture-overlay");
  if (!overlay) return;
  const counter = overlay.querySelector<HTMLElement>("[data-crane-progress]");
  if (counter) counter.textContent = `${current} / ${total}`;
  overlay.style.visibility = "visible";
}

function injectOverlay(totalSlices: number): void {
  // Remove any leftover overlay from a previous run.
  document.getElementById("crane-capture-overlay")?.remove();

  const div = document.createElement("div");
  div.id = "crane-capture-overlay";
  div.style.cssText = [
    "all: initial",
    "position: fixed",
    "top: 0",
    "left: 50%",
    "transform: translateX(-50%)",
    "z-index: 2147483647",
    "margin-top: 12px",
    "padding: 10px 16px",
    "background: rgba(15, 23, 42, 0.95)",
    "color: #f8fafc",
    "font: 500 13px/1.4 system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
    "border-radius: 999px",
    "box-shadow: 0 4px 14px rgba(15, 23, 42, 0.45)",
    "pointer-events: none",
    "user-select: none",
    "display: flex",
    "align-items: center",
    "gap: 10px",
  ].join(";");

  const dot = document.createElement("span");
  dot.style.cssText = [
    "display: inline-block",
    "width: 8px",
    "height: 8px",
    "border-radius: 50%",
    "background: #2563eb",
    "animation: crane-pulse 1.2s ease-in-out infinite",
  ].join(";");

  const label = document.createElement("span");
  label.textContent = "Crane is capturing the full page — please don't scroll or click";

  const counter = document.createElement("span");
  counter.dataset["craneProgress"] = "true";
  counter.style.cssText = "color: #94a3b8; font-variant-numeric: tabular-nums";
  counter.textContent = `0 / ${totalSlices}`;

  div.appendChild(dot);
  div.appendChild(label);
  div.appendChild(counter);

  // Inject keyframes for the pulse dot.
  const style = document.createElement("style");
  style.id = "crane-capture-overlay-style";
  style.textContent =
    "@keyframes crane-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }";

  document.body.appendChild(style);
  document.body.appendChild(div);

  // Block clicks while capture runs.
  document.body.dataset["craneOrigPointerEvents"] = document.body.style.pointerEvents;
  document.body.style.pointerEvents = "none";
  document.body.dataset["craneOrigCursor"] = document.body.style.cursor;
  document.body.style.cursor = "wait";
}

function restoreAfterCapture(originalScroll: number): void {
  const els = document.querySelectorAll<HTMLElement>("[data-crane-orig-pos]");
  for (const el of Array.from(els)) {
    el.style.position = el.dataset["craneOrigPos"] ?? "";
    delete el.dataset["craneOrigPos"];
  }
  if (document.documentElement.dataset["craneOrigScroll"] !== undefined) {
    document.documentElement.style.scrollBehavior =
      document.documentElement.dataset["craneOrigScroll"] ?? "";
    delete document.documentElement.dataset["craneOrigScroll"];
  }
  // Restore pointer-events / cursor and remove the banner.
  if (document.body.dataset["craneOrigPointerEvents"] !== undefined) {
    document.body.style.pointerEvents = document.body.dataset["craneOrigPointerEvents"] ?? "";
    delete document.body.dataset["craneOrigPointerEvents"];
  }
  if (document.body.dataset["craneOrigCursor"] !== undefined) {
    document.body.style.cursor = document.body.dataset["craneOrigCursor"] ?? "";
    delete document.body.dataset["craneOrigCursor"];
  }
  document.getElementById("crane-capture-overlay")?.remove();
  document.getElementById("crane-capture-overlay-style")?.remove();
  window.scrollTo(0, originalScroll);
}

async function stitchSlices(
  slices: { dataUrl: string; y: number }[],
  totalHeightCss: number,
  dpr: number,
): Promise<string> {
  if (slices.length === 0) throw new Error("No slices captured");
  const first = slices[0]!;
  const firstBlob = await (await fetch(first.dataUrl)).blob();
  const firstBitmap = await createImageBitmap(firstBlob);
  const widthPx = firstBitmap.width;
  const totalHeightPx = Math.max(firstBitmap.height, Math.round(totalHeightCss * dpr));

  const canvas = new OffscreenCanvas(widthPx, totalHeightPx);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("OffscreenCanvas 2d context unavailable");

  ctx.drawImage(firstBitmap, 0, Math.round(first.y * dpr));
  firstBitmap.close();

  for (let i = 1; i < slices.length; i++) {
    const slice = slices[i]!;
    const blob = await (await fetch(slice.dataUrl)).blob();
    const bitmap = await createImageBitmap(blob);
    ctx.drawImage(bitmap, 0, Math.round(slice.y * dpr));
    bitmap.close();
  }

  const outBlob = await canvas.convertToBlob({ type: "image/png" });
  return blobToDataUrl(outBlob);
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error ?? new Error("FileReader failed"));
    reader.readAsDataURL(blob);
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
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
  DETECT_LANGUAGE: handleDetectLanguage,
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
