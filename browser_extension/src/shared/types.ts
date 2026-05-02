// Shared types: API DTOs and the discriminated-union message protocol used
// between the side panel, background service worker, and content script.
//
// Keep this file the single source of truth for those shapes. The Python
// backend's JSON contract is mirrored here by hand; if you change a server
// response, update the matching DTO and the affected handlers will fail to
// type-check until you fix them.

// --- API DTOs --------------------------------------------------------------

export type LanguageSummary = {
  code: string;
  name: string;
};

export type PlatformSummary = {
  id: string;
  name: string;
  url_pattern: string;
};

export type FieldConfigType = "text" | "number" | "choice" | "boolean";

export type FieldConfigSummary = {
  field_name: string;
  label: string;
  field_type: FieldConfigType;
  required: boolean;
  choices: string[];
  order: number;
};

export type ProjectSummary = {
  id: string;
  name: string;
  slug: string;
  org_name: string;
  org_slug: string;
  languages: LanguageSummary[];
  platforms: PlatformSummary[];
  field_configs: FieldConfigSummary[];
};

export type CheckResult = {
  duplicate: boolean;
  record_id: string | null;
  id?: number;
  captured_at?: string;
};

export type CheckResponse = {
  results: Record<string, CheckResult>;
};

export type CaptureResponse = {
  id: number;
  record_id: string;
  form_url: string;
  duplicate_of: { id: number; record_id: string } | null;
};

export type SuggestItem = {
  platform: string;
  language: string;
  language_code: string;
  category: string;
  category_slug: string;
  last_searched: string | null;
  example_keyword: string | null;
  search_url: string | null;
};

export type SuggestResponse = {
  suggestions: SuggestItem[];
};

// --- Auth state persisted in chrome.storage.local --------------------------

export type AuthState = {
  token: string;
  email: string;
  baseUrl: string;
};

// --- Capture form payload --------------------------------------------------

export type Confidence = "" | "high" | "medium" | "low";

export type CapturePayload = {
  org_slug: string;
  project_slug: string;
  url: string;
  title: string;
  language: string;
  note: string;
  platform_id: string;
  date_of_post: string;          // YYYY-MM-DD or ""
  location_mentioned: string;
  probable_location: string;
  confidence: Confidence;
  extra_fields: Record<string, string | number | boolean | null>;
  // base64 data URL of the captured screenshot
  screenshot_data_url: string | null;
};

// --- Message protocol ------------------------------------------------------
//
// All messages are dispatched via `chrome.runtime.sendMessage` and routed by
// the background SW's dispatch table (`src/background/sw.ts`). Each request
// shape pairs with a response shape. Failures are returned as
// `{ ok: false, error: string }` rather than thrown — Chrome's messaging API
// drops thrown errors silently.

export type Ok<T> = { ok: true; data: T };
export type Err = { ok: false; error: string };
export type Result<T> = Ok<T> | Err;

export type InitiateAuthRequest = {
  type: "INITIATE_AUTH";
  // Override the persisted base URL before launching the web-auth flow.
  // If omitted, the SW resolves the URL from storage (or its default).
  baseUrl?: string;
};
export type InitiateAuthResponse = Result<AuthState>;

export type ClearAuthRequest = { type: "CLEAR_AUTH" };
export type ClearAuthResponse = Result<null>;

export type GetAuthStateRequest = { type: "GET_AUTH_STATE" };
export type GetAuthStateResponse = Result<AuthState | null>;

export type GetProjectsRequest = { type: "GET_PROJECTS" };
export type GetProjectsResponse = Result<ProjectSummary[]>;

export type CheckUrlRequest = {
  type: "CHECK_URL";
  url: string;
  projectId: string;
};
export type CheckUrlResponse = Result<CheckResult>;

export type CaptureRequest = {
  type: "CAPTURE";
  payload: CapturePayload;
};
export type CaptureMsgResponse = Result<CaptureResponse>;

export type SuggestRequest = {
  type: "GET_SUGGESTIONS";
  projectId: string;
};
export type SuggestMsgResponse = Result<SuggestItem[]>;

export type ScreenshotRequest = { type: "TAKE_SCREENSHOT" };
export type ScreenshotResponse = Result<string>; // data URL

export type DetectLanguageRequest = { type: "DETECT_LANGUAGE" };
export type DetectLanguageResponse = Result<string | null>; // ISO 639-1 code or null

// Background → content script broadcasts (no response expected).
export type PageUrlChangedBroadcast = {
  type: "PAGE_URL_CHANGED";
  url: string;
};

// Background → side panel broadcast (no response expected).
export type AuthBroadcast =
  | { type: "AUTH_UPDATED"; auth: AuthState }
  | { type: "AUTH_CLEARED" };

export type ExtensionMessage =
  | InitiateAuthRequest
  | ClearAuthRequest
  | GetAuthStateRequest
  | GetProjectsRequest
  | CheckUrlRequest
  | CaptureRequest
  | SuggestRequest
  | ScreenshotRequest
  | DetectLanguageRequest
  | PageUrlChangedBroadcast
  | AuthBroadcast;
