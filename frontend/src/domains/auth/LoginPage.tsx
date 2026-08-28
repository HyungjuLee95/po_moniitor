"use client";

import { FormEvent, useState } from "react";

import { apiFetch, apiUrl } from "../../core/api";
import { saveToken } from "../../core/session";
import type { User } from "../../core/types";

type LoginResponse = {
  access_token: string;
  user: User;
};

type AuthMode = "login" | "register" | "registered" | "forgot" | "reset";

const titles: Record<AuthMode, string> = {
  login: "운영 콘솔 로그인",
  register: "사용자 가입 신청",
  registered: "가입 신청 완료",
  forgot: "비밀번호 찾기",
  reset: "비밀번호 재설정",
};

export function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackTone, setFeedbackTone] = useState<"error" | "success">("error");
  const [mode, setMode] = useState<AuthMode>("login");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const changeMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setFeedback("");
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    setFeedback("");
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
      setFeedbackTone("error");
      setFeedback("계정 정보, 가입 승인 또는 백엔드 연결 상태를 확인해 주세요.");
    } finally {
      setPending(false);
    }
  };

  const register = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback("");
    if (password !== passwordConfirmation) {
      setFeedbackTone("error");
      setFeedback("비밀번호 확인 값이 일치하지 않습니다.");
      return;
    }
    setPending(true);
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username,
          display_name: displayName,
          password,
        }),
      });
      setMode("registered");
      setPassword("");
      setPasswordConfirmation("");
    } catch {
      setFeedbackTone("error");
      setFeedback("가입 신청에 실패했습니다. 아이디 중복과 입력 형식을 확인해 주세요.");
    } finally {
      setPending(false);
    }
  };

  const requestReset = async () => {
    setPending(true);
    setFeedback("");
    try {
      await apiFetch("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ username }),
      });
      setFeedbackTone("success");
      setFeedback("요청이 접수되었습니다. Administrator에게 1회 토큰을 전달받으세요.");
      setMode("reset");
    } catch {
      setFeedbackTone("error");
      setFeedback("요청을 처리하지 못했습니다.");
    } finally {
      setPending(false);
    }
  };

  const resetPassword = async () => {
    setPending(true);
    setFeedback("");
    try {
      await apiFetch("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token: resetToken, new_password: newPassword }),
      });
      setMode("login");
      setResetToken("");
      setNewPassword("");
      setFeedbackTone("success");
      setFeedback("비밀번호가 변경되었습니다. 새 비밀번호로 로그인하세요.");
    } catch {
      setFeedbackTone("error");
      setFeedback("토큰이 만료되었거나 올바르지 않습니다.");
    } finally {
      setPending(false);
    }
  };

  const formSubmit = mode === "login"
    ? submit
    : mode === "register"
      ? register
      : (event: FormEvent<HTMLFormElement>) => event.preventDefault();

  return (
    <main className="login-shell">
      <section className="login-story">
        <div className="brand-lockup">
          <span className="brand-symbol">PO</span>
          <div><b>MONITOR MAIN</b><small>SAP PROCESS ORCHESTRATION</small></div>
        </div>
        <div className="story-content">
          <p className="kicker">CONNECTED OPERATIONS</p>
          <h1>운영 흐름을<br />한눈에.</h1>
          <p>메시지, 채널, 시스템 상태와 인증서를 하나의 운영 콘솔에서 확인합니다.</p>
          <div className="login-capabilities" aria-label="주요 기능">
            <span>실시간 현황</span><span>채널 운영</span><span>메시지 추적</span><span>권한 관리</span>
          </div>
        </div>
        <div className="system-line"><i /> INTERNAL SYSTEM · AUTHORIZED ACCESS ONLY</div>
      </section>
      <section className="login-entry">
        <form className="login-card" onSubmit={formSubmit}>
          {(mode === "login" || mode === "register") && (
            <div className="auth-mode-tabs" role="tablist" aria-label="인증 방식">
              <button type="button" role="tab" aria-selected={mode === "login"} className={mode === "login" ? "active" : ""} onClick={() => changeMode("login")}>로그인</button>
              <button type="button" role="tab" aria-selected={mode === "register"} className={mode === "register" ? "active" : ""} onClick={() => changeMode("register")}>가입 신청</button>
            </div>
          )}
          <p className="kicker">SECURE ACCESS</p>
          <h2>{titles[mode]}</h2>
          <p className="supporting">
            {mode === "login" && "승인된 사내 계정으로 접속하세요."}
            {mode === "register" && "가입 후 Administrator가 역할과 접근 서버를 승인합니다."}
            {mode === "registered" && "일반 사용자로 등록되었으며 승인 전에는 로그인할 수 없습니다."}
            {(mode === "forgot" || mode === "reset") && "Administrator 승인형 1회 토큰을 사용합니다."}
          </p>

          {mode === "registered" ? (
            <div className="registration-complete" role="status">
              <span>✓</span>
              <div><b>신청이 접수되었습니다.</b><p>Administrator가 계정을 활성화하고 서버 접근 범위를 지정하면 로그인할 수 있습니다.</p></div>
            </div>
          ) : (
            <>
              {mode === "register" && <label><span>표시 이름</span><input value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" placeholder="홍길동" minLength={1} maxLength={100} required /></label>}
              {mode !== "reset" && <label>
                <span>사용자 ID</span>
                <input value={username} onChange={(event) => setUsername(event.target.value.toLowerCase())} autoComplete="username" placeholder="영문 소문자 · 숫자 · . _ -" pattern="[a-z0-9._-]{3,64}" required />
              </label>}
              {(mode === "login" || mode === "register") && <label>
                <span>비밀번호</span>
                <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder={mode === "register" ? "8자 이상" : "비밀번호 입력"} minLength={mode === "register" ? 8 : 1} required />
              </label>}
              {mode === "register" && <label><span>비밀번호 확인</span><input type="password" value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} autoComplete="new-password" placeholder="비밀번호 다시 입력" minLength={8} required /></label>}
              {mode === "reset" && <><label><span>1회 토큰</span><input value={resetToken} onChange={(event) => setResetToken(event.target.value)} required /></label><label><span>새 비밀번호</span><input type="password" minLength={8} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required /></label></>}
            </>
          )}

          {feedback && <p className={`form-feedback ${feedbackTone}`} role="alert">{feedback}</p>}
          {mode === "login" && <button className="primary-button" type="submit" disabled={pending}>{pending ? "연결 확인 중…" : "대시보드 열기"}</button>}
          {mode === "register" && <button className="primary-button" type="submit" disabled={pending}>{pending ? "신청 중…" : "가입 신청"}</button>}
          {mode === "registered" && <button className="primary-button" type="button" onClick={() => changeMode("login")}>로그인으로</button>}
          {mode === "forgot" && <button className="primary-button" type="button" onClick={() => void requestReset()} disabled={pending || !username}>재설정 요청</button>}
          {mode === "reset" && <button className="primary-button" type="button" onClick={() => void resetPassword()} disabled={pending || !resetToken || newPassword.length < 8}>비밀번호 재설정</button>}

          <div className="login-mode-actions">
            {(mode === "forgot" || mode === "reset") && <button type="button" onClick={() => changeMode("login")}>로그인으로</button>}
            {mode === "login" && <button type="button" onClick={() => changeMode("forgot")}>비밀번호 찾기</button>}
            {mode === "forgot" && <button type="button" onClick={() => changeMode("reset")}>토큰 입력</button>}
          </div>
          <p className="administrator-note"><b>Administrator</b> 계정은 시스템에서 한 개만 관리합니다.</p>
        </form>
      </section>
    </main>
  );
}
