"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "../core/api";
import { clearToken, readToken } from "../core/session";
import type { User } from "../core/types";
import { LoginPage } from "../domains/auth/LoginPage";
import { OperationsWorkspace } from "../domains/dashboard/OperationsWorkspace";

export function Application() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!readToken()) return;
    apiFetch<User>("/auth/me").then(setUser).catch(clearToken);
  }, []);

  if (!user) return <LoginPage onLogin={setUser} />;

  return (
    <OperationsWorkspace
      user={user}
      onLogout={() => {
        clearToken();
        setUser(null);
      }}
    />
  );
}
