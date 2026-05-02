// Side-panel state shape. Held in module scope by `index.ts`.

import type {
  AuthState,
  CaptureResponse,
  CheckResult,
  ProjectSummary,
  SuggestItem,
} from "@shared/types";

export type Screen = "loading" | "connect" | "capture" | "suggest" | "success";

export type ToastMode = "error" | "warn" | "success";
export type Toast = { mode: ToastMode; text: string };

export type AppState = {
  screen: Screen;
  busy: boolean;

  baseUrlDraft: string;

  auth: AuthState | null;
  projects: ProjectSummary[];
  selectedProjectId: string | null;
  selectedLanguage: string;

  currentUrl: string;
  currentTitle: string;
  screenshotDataUrl: string | null;

  note: string;
  duplicate: CheckResult | null;

  captureProgress: { current: number; total: number } | null;

  suggestions: SuggestItem[];
  lastCapture: CaptureResponse | null;
  toast: Toast | null;
  modalImage: string | null;
};

export function initialState(): AppState {
  return {
    screen: "loading",
    busy: false,
    baseUrlDraft: "http://localhost:8000",
    auth: null,
    projects: [],
    selectedProjectId: null,
    selectedLanguage: "",
    currentUrl: "",
    currentTitle: "",
    screenshotDataUrl: null,
    note: "",
    duplicate: null,
    captureProgress: null,
    suggestions: [],
    lastCapture: null,
    toast: null,
    modalImage: null,
  };
}
