import { runtimeConfig } from "./runtime";

export function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(runtimeConfig.tokenKey);
}

export function saveToken(token: string): void {
  window.sessionStorage.setItem(runtimeConfig.tokenKey, token);
}

export function clearToken(): void {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(runtimeConfig.tokenKey);
  }
}
