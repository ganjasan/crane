// Thin HTTP client around the Crane API. Reads token + base URL from
// chrome.storage.local on every call so a token rotation doesn't require
// a service-worker restart. All methods throw `ApiError` on non-2xx.

import { auth } from "./storage";
import type {
  AuthState,
  CapturePayload,
  CaptureResponse,
  CheckResponse,
  ProjectSummary,
  SuggestItem,
} from "./types";

export class ApiError extends Error {
  override readonly name = "ApiError";
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function requireAuth(): Promise<AuthState> {
  const a = await auth.load();
  if (!a) throw new ApiError(401, "Not connected");
  return a;
}

function authHeaders(a: AuthState): Record<string, string> {
  return { Authorization: `Bearer ${a.token}` };
}

async function parseError(resp: Response): Promise<string> {
  try {
    const body = await resp.json();
    if (body && typeof body === "object" && typeof body.error === "string") {
      return body.error;
    }
  } catch {
    /* fall through */
  }
  return `${resp.status} ${resp.statusText}`;
}

export const api = {
  async getProjects(): Promise<ProjectSummary[]> {
    const a = await requireAuth();
    const resp = await fetch(`${a.baseUrl}/api/v1/projects`, {
      headers: authHeaders(a),
    });
    if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
    const body = (await resp.json()) as { projects: ProjectSummary[] };
    return body.projects;
  },

  async checkUrl(url: string, projectId: string): Promise<CheckResponse["results"][string]> {
    const a = await requireAuth();
    const resp = await fetch(`${a.baseUrl}/api/v1/incidents/check`, {
      method: "POST",
      headers: { ...authHeaders(a), "Content-Type": "application/json" },
      body: JSON.stringify({ urls: [url], project_id: projectId }),
    });
    if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
    const body = (await resp.json()) as CheckResponse;
    return body.results[url] ?? { duplicate: false, record_id: null };
  },

  async getSuggestions(projectId: string): Promise<SuggestItem[]> {
    const a = await requireAuth();
    const resp = await fetch(
      `${a.baseUrl}/api/v1/coverage/suggest?project_id=${encodeURIComponent(projectId)}`,
      { headers: authHeaders(a) },
    );
    if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
    const body = (await resp.json()) as { suggestions: SuggestItem[] };
    return body.suggestions;
  },

  async capture(payload: CapturePayload): Promise<CaptureResponse> {
    const a = await requireAuth();
    const form = new FormData();
    form.append("org_slug", payload.org_slug);
    form.append("project_slug", payload.project_slug);
    form.append("url", payload.url);
    form.append("title", payload.title);
    form.append("language", payload.language);
    form.append("note", payload.note);
    if (payload.platform_id) form.append("platform_id", payload.platform_id);
    if (payload.date_of_post) form.append("date_of_post", payload.date_of_post);
    if (payload.location_mentioned) form.append("location_mentioned", payload.location_mentioned);
    if (payload.probable_location) form.append("probable_location", payload.probable_location);
    if (payload.confidence) form.append("confidence", payload.confidence);
    if (Object.keys(payload.extra_fields).length > 0) {
      form.append("extra_fields", JSON.stringify(payload.extra_fields));
    }
    if (payload.screenshot_data_url) {
      form.append(
        "screenshot",
        await dataUrlToBlob(payload.screenshot_data_url),
        "screenshot.png",
      );
    }
    const resp = await fetch(`${a.baseUrl}/api/v1/incidents/capture`, {
      method: "POST",
      headers: authHeaders(a), // Do NOT set Content-Type; the browser sets the boundary.
      body: form,
    });
    if (!resp.ok) throw new ApiError(resp.status, await parseError(resp));
    return (await resp.json()) as CaptureResponse;
  },
};

async function dataUrlToBlob(dataUrl: string): Promise<Blob> {
  const resp = await fetch(dataUrl);
  return resp.blob();
}
