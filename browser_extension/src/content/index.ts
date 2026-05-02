// Content script: injected into every page (host_permissions: <all_urls>).
//
// On load — and on each PAGE_URL_CHANGED broadcast from the background SW
// (which fires for SPA history-state navigations) — sends a CHECK_URL
// message. If the page is already in the user's last-used project, injects
// a small fixed-position toast in the corner of the viewport.
//
// Built as IIFE (see build.mjs) because MV3 forbids ES modules in content
// scripts. No imports from @shared at runtime — the file is bundled.

import { lastProject } from "@shared/storage";
import type { CheckUrlResponse } from "@shared/types";

const TOAST_ID = "crane-duplicate-toast";

async function check(url: string): Promise<void> {
  if (!/^https?:/i.test(url)) {
    removeToast();
    return;
  }
  const projectId = await lastProject.load();
  if (!projectId) return;

  const resp = (await chrome.runtime
    .sendMessage({ type: "CHECK_URL", url, projectId })
    .catch(() => null)) as CheckUrlResponse | null;
  if (!resp || !resp.ok) return;

  if (resp.data.duplicate) {
    showToast(resp.data.record_id ?? "—", resp.data.captured_at);
  } else {
    removeToast();
  }
}

function showToast(recordId: string, capturedAt: string | undefined): void {
  removeToast();
  const wrap = document.createElement("div");
  wrap.id = TOAST_ID;
  wrap.style.cssText = [
    "position:fixed",
    "right:16px",
    "bottom:16px",
    "z-index:2147483647",
    "background:#0f172a",
    "color:#f8fafc",
    "padding:10px 12px",
    "border-radius:8px",
    "box-shadow:0 4px 12px rgba(15,23,42,0.25)",
    "font:13px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif",
    "display:flex",
    "align-items:center",
    "gap:10px",
    "max-width:320px",
  ].join(";");

  const txt = document.createElement("span");
  const date = capturedAt ? capturedAt.slice(0, 10) : "";
  txt.textContent = `Already in Crane · ${recordId}${date ? ` · ${date}` : ""}`;
  wrap.appendChild(txt);

  const close = document.createElement("button");
  close.textContent = "×";
  close.setAttribute("aria-label", "Dismiss");
  close.style.cssText = [
    "background:transparent",
    "color:#cbd5e1",
    "border:none",
    "cursor:pointer",
    "font:16px/1 system-ui",
    "padding:0 4px",
  ].join(";");
  close.addEventListener("click", removeToast);
  wrap.appendChild(close);

  document.body.appendChild(wrap);
}

function removeToast(): void {
  const existing = document.getElementById(TOAST_ID);
  if (existing) existing.remove();
}

// Initial check on injection.
void check(window.location.href);

// React to SPA route changes broadcast by the background SW.
chrome.runtime.onMessage.addListener((rawMsg) => {
  const msg = rawMsg as { type: string; url?: string };
  if (msg.type === "PAGE_URL_CHANGED" && typeof msg.url === "string") {
    void check(msg.url);
  }
});
