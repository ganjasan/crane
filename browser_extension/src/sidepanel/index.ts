// Side panel entry point. Holds module-scope state, dispatches user actions,
// and re-renders on every state change.
//
// State machine:
//   - "loading" → reading auth from storage
//   - "connect" → no auth saved; prompt user to Connect
//   - "capture" → primary screen; capture form
//   - "suggest" → coverage gaps list
//   - "success" → just captured an incident, show confirmation card
//
// UI is vanilla DOM. `render(state, root)` is called after each `setState`.
// Top-level screen change replaces innerHTML; in-screen tweaks update text /
// hidden attributes inline.

import { render } from "./render";
import type { AppState, Screen, ToastMode } from "./state";
import { initialState } from "./state";
import type {
  AuthBroadcast,
  AuthState,
  CaptureMsgResponse,
  CheckResult,
  CheckUrlResponse,
  GetAuthStateResponse,
  GetProjectsResponse,
  ProjectSummary,
  ScreenshotResponse,
  SuggestMsgResponse,
} from "@shared/types";
import { baseUrl as baseUrlStore, lastProject } from "@shared/storage";

const root = document.getElementById("root")!;
let state: AppState = initialState();

function setState(patch: Partial<AppState>): void {
  state = { ...state, ...patch };
  render(state, root, dispatch);
}

// --- Dispatch table --------------------------------------------------------

export type Action =
  | { type: "CONNECT" }
  | { type: "EDIT_BASE_URL"; value: string }
  | { type: "DISCONNECT" }
  | { type: "SELECT_PROJECT"; projectId: string }
  | { type: "SELECT_LANGUAGE"; code: string }
  | { type: "EDIT_NOTE"; value: string }
  | { type: "RETAKE_SCREENSHOT" }
  | { type: "SUBMIT_CAPTURE"; force?: boolean }
  | { type: "GO_TO_SCREEN"; screen: Screen }
  | { type: "FETCH_SUGGESTIONS" }
  | { type: "OPEN_URL"; url: string }
  | { type: "DISMISS_TOAST" };

function dispatch(action: Action): void {
  switch (action.type) {
    case "CONNECT":
      void connect();
      return;
    case "EDIT_BASE_URL":
      setState({ baseUrlDraft: action.value });
      return;
    case "DISCONNECT":
      void disconnect();
      return;
    case "SELECT_PROJECT":
      void selectProject(action.projectId);
      return;
    case "SELECT_LANGUAGE":
      setState({ selectedLanguage: action.code });
      return;
    case "EDIT_NOTE":
      setState({ note: action.value });
      return;
    case "RETAKE_SCREENSHOT":
      void takeScreenshot();
      return;
    case "SUBMIT_CAPTURE":
      void submitCapture(Boolean(action.force));
      return;
    case "GO_TO_SCREEN":
      setState({ screen: action.screen, toast: null });
      if (action.screen === "suggest") void fetchSuggestions();
      return;
    case "FETCH_SUGGESTIONS":
      void fetchSuggestions();
      return;
    case "OPEN_URL":
      void chrome.tabs.create({ url: action.url });
      return;
    case "DISMISS_TOAST":
      setState({ toast: null });
      return;
  }
}

// --- Async actions ---------------------------------------------------------

async function bootstrap(): Promise<void> {
  setState({ screen: "loading" });
  const persistedBaseUrl = await baseUrlStore.load();
  if (persistedBaseUrl) setState({ baseUrlDraft: persistedBaseUrl });
  const authResp = (await chrome.runtime.sendMessage({
    type: "GET_AUTH_STATE",
  })) as GetAuthStateResponse;
  if (!authResp.ok || !authResp.data) {
    setState({ screen: "connect", auth: null });
    return;
  }
  await enterCaptureScreen(authResp.data);
}

async function connect(): Promise<void> {
  const baseUrl = state.baseUrlDraft.trim().replace(/\/$/, "");
  if (!/^https?:\/\//i.test(baseUrl)) {
    setState({
      toast: { mode: "error", text: "Base URL must start with http:// or https://" },
    });
    return;
  }
  setState({ busy: true, toast: null });
  const resp = (await chrome.runtime.sendMessage({
    type: "INITIATE_AUTH",
    baseUrl,
  })) as { ok: true; data: AuthState } | { ok: false; error: string };
  if (!resp.ok) {
    setState({ busy: false, toast: { mode: "error", text: resp.error } });
    return;
  }
  await enterCaptureScreen(resp.data);
}

async function disconnect(): Promise<void> {
  await chrome.runtime.sendMessage({ type: "CLEAR_AUTH" });
  setState({
    screen: "connect",
    auth: null,
    projects: [],
    selectedProjectId: null,
    selectedLanguage: "",
    note: "",
    screenshotDataUrl: null,
    duplicate: null,
    suggestions: [],
    toast: null,
    busy: false,
  });
}

async function enterCaptureScreen(authState: AuthState): Promise<void> {
  setState({ auth: authState, busy: true, screen: "loading" });
  const projectsResp = (await chrome.runtime.sendMessage({
    type: "GET_PROJECTS",
  })) as GetProjectsResponse;
  if (!projectsResp.ok) {
    setState({
      busy: false,
      screen: "connect",
      toast: { mode: "error", text: projectsResp.error },
    });
    return;
  }
  const projects = projectsResp.data;
  const lastProjectId = await lastProject.load();
  const initialProject =
    projects.find((p) => p.id === lastProjectId) ?? projects[0] ?? null;

  setState({
    busy: false,
    projects,
    screen: "capture",
    selectedProjectId: initialProject?.id ?? null,
    selectedLanguage: initialProject?.languages[0]?.code ?? "",
    duplicate: null,
  });
  await refreshTabContext();
  if (initialProject) await checkCurrentTab(initialProject);
}

async function selectProject(projectId: string): Promise<void> {
  const project = state.projects.find((p) => p.id === projectId);
  if (!project) return;
  await lastProject.save(projectId);
  setState({
    selectedProjectId: projectId,
    selectedLanguage: project.languages[0]?.code ?? "",
    duplicate: null,
  });
  await checkCurrentTab(project);
}

async function refreshTabContext(): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  setState({
    currentUrl: tab?.url ?? "",
    currentTitle: tab?.title ?? "",
  });
  if (tab && /^https?:/i.test(tab.url ?? "")) {
    await takeScreenshot();
  } else {
    setState({ screenshotDataUrl: null });
  }
}

async function takeScreenshot(): Promise<void> {
  const resp = (await chrome.runtime.sendMessage({
    type: "TAKE_SCREENSHOT",
  })) as ScreenshotResponse;
  setState({ screenshotDataUrl: resp.ok ? resp.data : null });
}

async function checkCurrentTab(project: ProjectSummary): Promise<void> {
  const url = state.currentUrl;
  if (!url || !/^https?:/i.test(url)) {
    setState({ duplicate: null });
    return;
  }
  const resp = (await chrome.runtime.sendMessage({
    type: "CHECK_URL",
    url,
    projectId: project.id,
  })) as CheckUrlResponse;
  if (resp.ok && resp.data.duplicate) {
    setState({ duplicate: resp.data });
  } else {
    setState({ duplicate: null });
  }
}

async function submitCapture(force: boolean): Promise<void> {
  const project = state.projects.find((p) => p.id === state.selectedProjectId);
  if (!project) {
    setState({ toast: { mode: "error", text: "Select a project first" } });
    return;
  }
  if (!state.currentUrl) {
    setState({ toast: { mode: "error", text: "No active tab URL" } });
    return;
  }

  // Pre-flight duplicate check unless the user already chose "Submit anyway".
  if (!force) {
    const checkResp = (await chrome.runtime.sendMessage({
      type: "CHECK_URL",
      url: state.currentUrl,
      projectId: project.id,
    })) as CheckUrlResponse;
    if (checkResp.ok && checkResp.data.duplicate) {
      setState({ duplicate: checkResp.data });
      return;
    }
  }

  setState({ busy: true, toast: null });
  const captureResp = (await chrome.runtime.sendMessage({
    type: "CAPTURE",
    payload: {
      org_slug: project.org_slug,
      project_slug: project.slug,
      url: state.currentUrl,
      title: state.currentTitle,
      language: state.selectedLanguage,
      note: state.note,
      screenshot_data_url: state.screenshotDataUrl,
    },
  })) as CaptureMsgResponse;
  if (!captureResp.ok) {
    setState({ busy: false, toast: { mode: "error", text: captureResp.error } });
    return;
  }
  setState({
    busy: false,
    screen: "success",
    lastCapture: captureResp.data,
    note: "",
    duplicate: null,
  });
}

async function fetchSuggestions(): Promise<void> {
  const projectId = state.selectedProjectId;
  if (!projectId) return;
  setState({ busy: true, suggestions: [] });
  const resp = (await chrome.runtime.sendMessage({
    type: "GET_SUGGESTIONS",
    projectId,
  })) as SuggestMsgResponse;
  if (!resp.ok) {
    setState({ busy: false, toast: { mode: "error", text: resp.error } });
    return;
  }
  setState({ busy: false, suggestions: resp.data });
}

// --- Background broadcasts -------------------------------------------------

chrome.runtime.onMessage.addListener((rawMsg) => {
  const msg = rawMsg as AuthBroadcast | { type: string };
  if (msg.type === "AUTH_UPDATED") {
    void enterCaptureScreen((msg as { auth: AuthState }).auth);
  } else if (msg.type === "AUTH_CLEARED") {
    setState({ screen: "connect", auth: null });
  } else if (msg.type === "CAPTURE_PROGRESS") {
    const { current, total } = msg as unknown as { current: number | null; total: number | null };
    if (current == null || total == null) {
      setState({ captureProgress: null });
    } else {
      setState({ captureProgress: { current, total } });
    }
  }
});

// Re-check the active tab when the user switches tabs while panel is open.
chrome.tabs.onActivated.addListener(() => {
  if (state.screen === "capture") void refreshAfterTabChange();
});
chrome.tabs.onUpdated.addListener((_id, changeInfo, tab) => {
  if (state.screen !== "capture") return;
  if (!tab.active) return;
  if (changeInfo.url || changeInfo.status === "complete") {
    void refreshAfterTabChange();
  }
});

async function refreshAfterTabChange(): Promise<void> {
  await refreshTabContext();
  const project = state.projects.find((p) => p.id === state.selectedProjectId);
  if (project) await checkCurrentTab(project);
}

// --- Suppress unused type-only imports lint --------------------------------
// (kept here so future maintainers see at a glance which types travel through)
export type _Unused = ToastMode | CheckResult;

// Boot.
void bootstrap();
