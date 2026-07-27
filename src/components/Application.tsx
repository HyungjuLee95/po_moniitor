"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "../api/client";
import { clearToken, readToken } from "../auth/session";
import type { User } from "../types";
import { Dashboard } from "./Dashboard";
import { LoginPage } from "./LoginPage";

export function Application() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!readToken()) return;
    apiFetch<User>("/auth/me")
      .then(setUser)
      .catch(clearToken);
  }, []);

  if (!user) return <LoginPage onLogin={setUser} />;

  return (
    <Dashboard
      user={user}
      onLogout={() => {
        clearToken();
        setUser(null);
      }}
    />
  );
}
