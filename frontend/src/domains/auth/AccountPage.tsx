"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User } from "../../core/types";


export function AccountPage({ user }: { user: User }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [notice, setNotice] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setNotice("새 비밀번호 확인이 일치하지 않습니다.");
      return;
    }
    try {
      await apiFetch("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword("");
      setNotice("비밀번호를 변경했습니다.");
    } catch {
      setNotice("현재 비밀번호를 확인하거나 새 비밀번호 조건을 확인하세요.");
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">MY ACCOUNT</p><h2>내 계정</h2><p>{user.display_name} · {user.role}</p></div></header>
      <form className="account-form detail-card" onSubmit={submit}>
        <h3>비밀번호 직접 변경</h3>
        <label><span>현재 비밀번호</span><input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required /></label>
        <label><span>새 비밀번호</span><input type="password" minLength={8} value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required /></label>
        <label><span>새 비밀번호 확인</span><input type="password" minLength={8} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required /></label>
        {notice && <p className="inline-notice">{notice}</p>}
        <button className="primary-button">비밀번호 변경</button>
      </form>
    </section>
  );
}
