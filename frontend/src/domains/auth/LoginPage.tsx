"use client";

import { FormEvent, useState } from "react";

import { apiUrl } from "../../core/api";
import { saveToken } from "../../core/session";
import type { User } from "../../core/types";

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
      setError("계정 정보 또는 백엔드 연결 상태를 확인해 주세요.");
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="login-shell">
      <section className="login-story">
        <div className="brand-lockup">
          <span className="brand-symbol">PO</span>
          <div><b>MONITOR MAIN</b><small>SAP PROCESS ORCHESTRATION</small></div>
        </div>
        <div className="story-content">
          <p className="kicker">CONNECTED OPERATIONS</p>
          <h1>흐름은 선명하게.<br />대응은 더 빠르게.</h1>
          <p>서버부터 채널, 메시지와 장애까지 하나의 운영 맥락으로 연결합니다.</p>
        </div>
        <div className="system-line"><i /> INTERNAL SYSTEM · AUTHORIZED ACCESS ONLY</div>
      </section>
      <section className="login-entry">
        <form className="login-card" onSubmit={submit}>
          <p className="kicker">WELCOME BACK</p>
          <h2>운영 콘솔 로그인</h2>
          <p className="supporting">권한이 등록된 사내 계정으로 접속하세요.</p>
          <label>
            <span>사용자 ID</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder="사번 또는 계정명" required />
          </label>
          <label>
            <span>비밀번호</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" placeholder="비밀번호 입력" required />
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={pending}>{pending ? "연결 확인 중…" : "콘솔 시작하기"}</button>
          <small className="login-help">접속 문제가 반복되면 시스템 관리자에게 문의하세요.</small>
        </form>
      </section>
    </main>
  );
}
