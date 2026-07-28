import { readToken } from "./session";
import { runtimeConfig } from "./runtime";

export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${runtimeConfig.apiBaseUrl}${runtimeConfig.apiPrefix}${normalized}`;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = readToken();
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const error = new Error(`API ${response.status}`);
    Object.assign(error, { status: response.status });
    throw error;
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
