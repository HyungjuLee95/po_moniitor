"use client";

import { FormEvent, useState } from "react";

import { apiFetch, apiUrl } from "../../core/api";
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
  const [mode, setMode] = useState<"login" | "forgot" | "reset">("login");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

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

  const requestReset = async () => {
    setPending(true); setError("");
    try {
      await apiFetch("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ username }),
      });
      setError("요청이 접수되었습니다. 관리자에게 1회 토큰을 전달받으세요.");
      setMode("reset");
    } catch {
      setError("요청을 처리하지 못했습니다.");
    } finally { setPending(false); }
  };

  const resetPassword = async () => {
    setPending(true); setError("");
    try {
      await apiFetch("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token: resetToken, new_password: newPassword }),
      });
      setMode("login"); setResetToken(""); setNewPassword("");
      setError("비밀번호가 변경되었습니다. 새 비밀번호로 로그인하세요.");
    } catch {
      setError("토큰이 만료되었거나 올바르지 않습니다.");
    } finally { setPending(false); }
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
        <form className="login-card" onSubmit={mode === "login" ? submit : (event) => event.preventDefault()}>
          <p className="kicker">WELCOME BACK</p>
          <h2>{mode === "login" ? "운영 콘솔 로그인" : mode === "forgot" ? "비밀번호 찾기" : "비밀번호 재설정"}</h2>
          <p className="supporting">{mode === "login" ? "권한이 등록된 사내 계정으로 접속하세요." : "관리자 승인형 1회 토큰을 사용합니다."}</p>
          {mode !== "reset" && <label>
            <span>사용자 ID</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder="사번 또는 계정명" required />
          </label>}
          {mode === "login" && <label>
            <span>비밀번호</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" placeholder="비밀번호 입력" required />
          </label>}
          {mode === "reset" && <><label><span>1회 토큰</span><input value={resetToken} onChange={(event) => setResetToken(event.target.value)} required /></label><label><span>새 비밀번호</span><input type="password" minLength={8} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required /></label></>}
          {error && <p className="form-error" role="alert">{error}</p>}
          {mode === "login" && <button className="primary-button" type="submit" disabled={pending}>{pending ? "연결 확인 중…" : "콘솔 시작하기"}</button>}
          {mode === "forgot" && <button className="primary-button" type="button" onClick={() => void requestReset()} disabled={pending || !username}>관리자 승인 요청</button>}
          {mode === "reset" && <button className="primary-button" type="button" onClick={() => void resetPassword()} disabled={pending || !resetToken || newPassword.length < 8}>비밀번호 재설정</button>}
          <div className="login-mode-actions">{mode !== "login" && <button type="button" onClick={() => { setMode("login"); setError(""); }}>로그인으로</button>}{mode === "login" && <button type="button" onClick={() => { setMode("forgot"); setError(""); }}>비밀번호 찾기</button>}{mode === "forgot" && <button type="button" onClick={() => setMode("reset")}>토큰 입력</button>}</div>
        </form>
      </section>
    </main>
  );
}
