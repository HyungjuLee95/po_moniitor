import { readToken } from "./session";
import { runtimeConfig } from "./runtime";

export type ApiRequestInit = RequestInit & {
  timeoutMs?: number;
};

export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${runtimeConfig.apiBaseUrl}${runtimeConfig.apiPrefix}${normalized}`;
}

export async function apiRequest(path: string, init?: ApiRequestInit): Promise<Response> {
  const token = readToken();
  const { timeoutMs = 30_000, signal, ...requestInit } = init ?? {};
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort(signal?.reason);
  if (signal?.aborted) {
    abortFromCaller();
  } else {
    signal?.addEventListener("abort", abortFromCaller, { once: true });
  }
  const timeoutId = window.setTimeout(
    () => controller.abort(new Error(`API request timed out after ${timeoutMs}ms`)),
    timeoutMs,
  );

  try {
    const response = await fetch(apiUrl(path), {
      ...requestInit,
      signal: controller.signal,
      headers: {
        ...(!(requestInit.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...requestInit.headers,
      },
    });
    if (!response.ok) {
      const error = new Error(`API ${response.status}`);
      Object.assign(error, { status: response.status });
      throw error;
    }
    return response;
  } finally {
    window.clearTimeout(timeoutId);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

export async function apiFetch<T>(path: string, init?: ApiRequestInit): Promise<T> {
  const response = await apiRequest(path, init);
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
