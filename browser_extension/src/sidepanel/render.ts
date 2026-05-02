// Vanilla DOM renderer for the side panel. Builds a tree with createElement
// and textContent — never uses innerHTML — so user-controlled values
// (project/org names, URL, notes, error text) cannot inject markup.
//
// On each render() call we replace #root's children with a fresh tree.
// Inputs preserve their typed values across re-renders because the renderer
// reads `state.note`, `state.selectedLanguage`, etc. when constructing the
// elements.

import type { AppState } from "./state";
import type { Action } from "./index";

type Dispatch = (action: Action) => void;

type Props = Record<string, string | number | boolean | EventListener | undefined>;
type Child = Node | string | null | false | undefined;

function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Props = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = String(v);
    else if (k === "value" && (el instanceof HTMLInputElement || el instanceof HTMLSelectElement || el instanceof HTMLTextAreaElement)) {
      el.value = String(v);
    } else if (k === "selected" && el instanceof HTMLOptionElement) {
      el.selected = Boolean(v);
    } else if (k === "disabled") {
      (el as HTMLButtonElement | HTMLSelectElement | HTMLInputElement | HTMLTextAreaElement).disabled = Boolean(v);
    } else if (k === "style") {
      el.setAttribute("style", String(v));
    } else if (typeof v === "function" && k.startsWith("on")) {
      el.addEventListener(k.slice(2).toLowerCase(), v as EventListener);
    } else if (typeof v === "boolean") {
      if (v) el.setAttribute(k, "");
    } else {
      el.setAttribute(k, String(v));
    }
  }
  for (const c of children) {
    if (c == null || c === false) continue;
    el.append(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return el;
}

export function render(state: AppState, root: HTMLElement, dispatch: Dispatch): void {
  const tree = h("div", {},
    renderTopbar(state),
    state.screen === "capture" || state.screen === "suggest" ? renderTabs(state, dispatch) : null,
    h("div", { class: "screen" },
      renderScreen(state, dispatch),
      renderToast(state, dispatch),
    ),
  );
  root.replaceChildren(...Array.from(tree.childNodes));
}

function renderTopbar(state: AppState): HTMLElement {
  return h("div", { class: "topbar" },
    h("span", { class: "brand" }, "Crane"),
    state.auth ? h("span", { class: "who" }, state.auth.email) : null,
  );
}

function renderTabs(state: AppState, dispatch: Dispatch): HTMLElement {
  const isCapture = state.screen === "capture";
  return h("div", { class: "tabs" },
    h("button", {
      class: `tab ${isCapture ? "active" : ""}`,
      onClick: () => dispatch({ type: "GO_TO_SCREEN", screen: "capture" }),
    }, "Capture"),
    h("button", {
      class: `tab ${!isCapture ? "active" : ""}`,
      onClick: () => dispatch({ type: "GO_TO_SCREEN", screen: "suggest" }),
    }, "Suggestions"),
  );
}

function renderScreen(state: AppState, dispatch: Dispatch): Node {
  switch (state.screen) {
    case "loading":
      return h("div", { class: "card" }, h("p", { class: "muted" }, "Loading…"));
    case "connect":
      return renderConnect(state, dispatch);
    case "capture":
      return renderCapture(state, dispatch);
    case "suggest":
      return renderSuggest(state, dispatch);
    case "success":
      return renderSuccess(state, dispatch);
  }
}

function renderConnect(state: AppState, dispatch: Dispatch): HTMLElement {
  const baseUrlInput = h("input", {
    type: "text",
    placeholder: "https://crane.your-host.com",
    spellcheck: false,
    onInput: (ev: Event) =>
      dispatch({ type: "EDIT_BASE_URL", value: (ev.target as HTMLInputElement).value }),
  });
  baseUrlInput.value = state.baseUrlDraft;

  return h("div", { class: "card" },
    h("h2", { class: "heading" }, "Connect to Crane"),
    h("p", { class: "muted" },
      "Point the extension at your Crane host, then sign in. A token is issued automatically and stored locally.",
    ),
    h("div", { style: "display:flex;flex-direction:column;gap:0.75rem;margin-top:0.75rem;" },
      h("label", { class: "field" },
        h("span", {}, "Crane base URL"),
        baseUrlInput,
      ),
      h("button", {
        class: "btn btn-primary",
        disabled: state.busy,
        onClick: () => dispatch({ type: "CONNECT" }),
      }, state.busy ? "Connecting…" : "Connect"),
    ),
  );
}

function renderCapture(state: AppState, dispatch: Dispatch): HTMLElement {
  const project = state.projects.find((p) => p.id === state.selectedProjectId);
  const noProjects = state.projects.length === 0;

  const projectSelect = h(
    "select",
    {
      disabled: noProjects,
      onChange: (ev: Event) =>
        dispatch({ type: "SELECT_PROJECT", projectId: (ev.target as HTMLSelectElement).value }),
    },
    ...state.projects.map((p) =>
      h("option", { value: p.id, selected: p.id === state.selectedProjectId },
        `${p.org_name} · ${p.name}`,
      ),
    ),
    state.projects.length === 0 ? h("option", {}, "—") : null,
  );

  const langSelect = h(
    "select",
    {
      disabled: !project || project.languages.length === 0,
      onChange: (ev: Event) =>
        dispatch({ type: "SELECT_LANGUAGE", code: (ev.target as HTMLSelectElement).value }),
    },
    ...((project?.languages ?? []).map((l) =>
      h("option", { value: l.code, selected: l.code === state.selectedLanguage }, l.name),
    )),
    !project || project.languages.length === 0 ? h("option", { value: "" }, "—") : null,
  );

  const noteArea = h("textarea", {
    placeholder: "Optional context for the reviewer",
    onInput: (ev: Event) =>
      dispatch({ type: "EDIT_NOTE", value: (ev.target as HTMLTextAreaElement).value }),
  });
  noteArea.value = state.note;

  const canCapture = !!state.currentUrl && /^https?:/i.test(state.currentUrl);
  const screenshotEl = state.captureProgress
    ? renderCaptureProgress(state.captureProgress)
    : state.screenshotDataUrl
      ? h("img", { class: "screenshot", src: state.screenshotDataUrl, alt: "page screenshot" })
      : renderScreenshotPlaceholder(canCapture, dispatch);

  const dupBlock = state.duplicate
    ? h("div", { class: "alert alert-warn" },
        h("strong", {}, "Already in Crane. "),
        state.duplicate.record_id ? `Record ${state.duplicate.record_id}` : "",
        state.duplicate.captured_at ? ` · ${state.duplicate.captured_at.slice(0, 10)}` : "",
        h("div", { class: "row", style: "margin-top: 0.5rem;" },
          h("button", {
            class: "btn btn-ghost",
            onClick: () => openDuplicate(state, dispatch),
          }, "Open existing"),
          h("button", {
            class: "btn btn-primary",
            disabled: state.busy,
            onClick: () => dispatch({ type: "SUBMIT_CAPTURE", force: true }),
          }, "Submit anyway"),
        ),
      )
    : null;

  const noProjectsAlert = noProjects
    ? h("div", { class: "alert alert-warn" }, "You're not a member of any project yet.")
    : null;

  return h("div", {},
    h("div", { class: "card" },
      h("h2", { class: "heading" }, "Capture evidence"),
      h("p", { class: "muted", style: "word-break:break-all;" }, state.currentUrl || "—"),
      noProjectsAlert,
      dupBlock,
      screenshotEl,
      h("div", { style: "display:flex;flex-direction:column;gap:0.75rem;margin-top:0.75rem;" },
        h("label", { class: "field" }, h("span", {}, "Project"), projectSelect),
        h("label", { class: "field" }, h("span", {}, "Language"), langSelect),
        h("label", { class: "field" }, h("span", {}, "Notes"), noteArea),
        h("div", { class: "row" },
          state.screenshotDataUrl
            ? h("button", {
                class: "btn btn-ghost",
                onClick: () => dispatch({ type: "RETAKE_SCREENSHOT" }),
              }, "Retake screenshot")
            : null,
          h("span", { class: "grow" }),
          h("button", {
            class: "btn btn-primary",
            disabled: state.busy || noProjects,
            onClick: () => dispatch({ type: "SUBMIT_CAPTURE" }),
          }, state.busy ? "Submitting…" : "Capture"),
        ),
      ),
    ),
    h("div", { class: "row", style: "justify-content:flex-end;" },
      h("button", {
        class: "btn-link",
        onClick: () => dispatch({ type: "DISCONNECT" }),
      }, "Disconnect"),
    ),
  );
}

function renderSuggest(state: AppState, dispatch: Dispatch): HTMLElement {
  if (state.busy && state.suggestions.length === 0) {
    return h("div", { class: "card" }, h("p", { class: "muted" }, "Loading suggestions…"));
  }
  if (state.suggestions.length === 0) {
    return h("div", { class: "card" },
      h("h2", { class: "heading" }, "Coverage gaps"),
      h("p", { class: "muted" },
        "No suggestions available — configure platforms, languages, and categories in your project to populate the coverage matrix.",
      ),
      h("div", { class: "row" },
        h("button", {
          class: "btn btn-ghost",
          onClick: () => dispatch({ type: "FETCH_SUGGESTIONS" }),
        }, "Refresh"),
      ),
    );
  }
  return h("div", { class: "card" },
    h("h2", { class: "heading" }, "Top 3 stalest cells"),
    h("p", { class: "muted" }, "Coverage gaps for the selected project, oldest first."),
    h("div", { class: "suggest-list", style: "margin-top:0.5rem;" },
      ...state.suggestions.map((s, idx) =>
        h("div", { class: "suggest-item" },
          h("div", { class: "meta" }, `${s.platform} · ${s.language} · ${s.category}`),
          s.example_keyword
            ? h("span", { class: "term" }, s.example_keyword)
            : h("span", { class: "muted" }, "No active keyword in this category"),
          h("div", { class: "meta" },
            s.last_searched ? `Last searched ${s.last_searched.slice(0, 10)}` : "Never searched",
          ),
          h("div", { class: "row", style: "margin-top:0.25rem;" },
            s.search_url
              ? h("button", {
                  class: "btn btn-primary",
                  onClick: () => dispatch({ type: "OPEN_URL", url: s.search_url! }),
                }, "Open search")
              : null,
            idx === 0
              ? h("button", {
                  class: "btn btn-ghost",
                  onClick: () => dispatch({ type: "FETCH_SUGGESTIONS" }),
                }, "Refresh")
              : null,
          ),
        ),
      ),
    ),
  );
}

function renderSuccess(state: AppState, dispatch: Dispatch): HTMLElement {
  const last = state.lastCapture;
  if (!last) return renderCapture(state, dispatch);
  return h("div", { class: "card" },
    h("div", { class: "alert alert-success" },
      "Captured as ",
      h("strong", {}, last.record_id),
      ".",
      last.duplicate_of ? ` Linked to existing ${last.duplicate_of.record_id}.` : "",
    ),
    h("div", { class: "row", style: "margin-top:0.75rem;" },
      h("button", {
        class: "btn btn-primary",
        onClick: () => dispatch({ type: "OPEN_URL", url: last.form_url }),
      }, "Open in Crane"),
      h("button", {
        class: "btn btn-ghost",
        onClick: () => dispatch({ type: "GO_TO_SCREEN", screen: "capture" }),
      }, "Capture another"),
    ),
  );
}

function renderToast(state: AppState, dispatch: Dispatch): Node | null {
  if (!state.toast) return null;
  const cls =
    state.toast.mode === "error"
      ? "alert-error"
      : state.toast.mode === "warn"
        ? "alert-warn"
        : "alert-success";
  return h("div", { class: `alert ${cls}` },
    state.toast.text,
    " ",
    h("button", {
      class: "btn-link",
      style: "margin-left:0.5rem;",
      onClick: () => dispatch({ type: "DISMISS_TOAST" }),
    }, "Dismiss"),
  );
}

function renderScreenshotPlaceholder(canCapture: boolean, dispatch: Dispatch): HTMLElement {
  if (!canCapture) {
    return h("div",
      {
        class: "screenshot",
        style:
          "display:flex;align-items:center;justify-content:center;color:var(--crane-muted);font-size:12px;",
      },
      "Screenshots are not available on this page.",
    );
  }
  return h("button",
    {
      type: "button",
      class: "screenshot",
      style:
        "display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.4rem;cursor:pointer;border:1px dashed var(--crane-border);background:#f8fafc;color:var(--crane-primary);font-size:13px;font-weight:500;padding:0;",
      onClick: () => dispatch({ type: "RETAKE_SCREENSHOT" }),
    },
    h("span", { style: "font-size:18px;line-height:1;" }, "📸"),
    h("span", {}, "Create screenshot"),
    h("span",
      { style: "color:var(--crane-muted);font-weight:400;font-size:11px;" },
      "Captures the full page top-to-bottom",
    ),
  );
}

function renderCaptureProgress(progress: { current: number; total: number }): HTMLElement {
  const pct = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
  return h("div",
    {
      class: "screenshot",
      style:
        "display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.4rem;color:var(--crane-text);font-size:12px;background:#0f172a;color:#f8fafc;",
    },
    h("div", { style: "font-weight:500;" }, "Capturing full page…"),
    h("div", { style: "color:#94a3b8;font-variant-numeric:tabular-nums;" },
      `${progress.current} / ${progress.total}`,
    ),
    h("div",
      {
        style:
          "width:80%;height:4px;background:rgba(248,250,252,0.15);border-radius:2px;overflow:hidden;",
      },
      h("div", {
        style:
          `width:${pct}%;height:100%;background:#2563eb;transition:width 0.3s ease;`,
      }),
    ),
    h("div",
      { style: "color:#64748b;font-size:11px;text-align:center;max-width:90%;" },
      "Page is scrolling — please don't scroll or click.",
    ),
  );
}

// --- Helpers ---------------------------------------------------------------

function openDuplicate(state: AppState, dispatch: Dispatch): void {
  const dup = state.duplicate;
  if (!dup || dup.id == null || !state.auth) return;
  const project = state.projects.find((p) => p.id === state.selectedProjectId);
  if (!project) return;
  const base = state.auth.baseUrl.replace(/\/$/, "");
  const url = `${base}/${project.org_slug}/${project.slug}/incidents/${dup.id}/`;
  dispatch({ type: "OPEN_URL", url });
}
