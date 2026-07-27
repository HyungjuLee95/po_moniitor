"use client";

import { FormEvent, useState } from "react";

import { apiUrl } from "../api/client";
import { saveToken } from "../auth/session";
import type { User } from "../types";

type LoginResponse = {
  access_token: string;
  user: User;
};

export function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const response = await fetch(apiUrl("/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });
      if (!response.ok) throw new Error("login failed");
      const payload = await response.json() as LoginResponse;
      saveToken(payload.access_token);
      onLogin(payload.user);
    } catch {
      setError("계정 정보를 확인해 주세요.");
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-intro">
        <div className="product-mark">PO</div>
        <p>SAP PROCESS ORCHESTRATION</p>
        <h1>흐름을 읽고,<br />문제를 먼저 발견합니다.</h1>
        <p className="intro-copy">서버·채널·메시지·Collector를 하나의 운영 기준으로 연결한 모니터링 콘솔입니다.</p>
        <div className="intro-status"><span /> INTERNAL OPERATIONS CONSOLE</div>
      </section>
      <section className="login-panel">
        <div className="login-box">
          <p className="eyebrow">PO MONITOR MAIN</p>
          <h2>운영 콘솔 로그인</h2>
          <p className="muted">승인된 계정으로 로그인해 주세요.</p>
          <form onSubmit={submit}>
            <label>사용자 ID<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required /></label>
            <label>비밀번호<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button type="submit" disabled={pending}>{pending ? "확인 중…" : "로그인"}</button>
          </form>
          <small>권한에 따라 조회·운영·관리 메뉴가 구분됩니다.</small>
        </div>
      </section>
    </main>
  );
}
