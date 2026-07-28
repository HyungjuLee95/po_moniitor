"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { ManagedUser, PoServer, Role } from "../../core/types";


const roleLabels: Record<Role, string> = {
  ADMIN: "admin",
  OPERATOR: "관리자",
  VIEWER: "일반",
};

const roleDescriptions: Record<Role, string> = {
  ADMIN: "사용자·환경 설정을 포함한 전체 권한",
  OPERATOR: "모니터링 조회와 채널 운영 권한",
  VIEWER: "모니터링과 Audit 조회 전용",
};

export function UserManagementPanel({ servers, currentUsername }: { servers: PoServer[]; currentUsername: string }) {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [role, setRole] = useState<Role>("VIEWER");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [resetPasswords, setResetPasswords] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiFetch<{ data: ManagedUser[] }>("/auth/users");
      setUsers(payload.data);
    } catch {
      setNotice("사용자 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await apiFetch("/auth/users", {
        method: "POST",
        body: JSON.stringify({
          username,
          display_name: displayName,
          temporary_password: temporaryPassword,
          role,
          server_sids: [],
        }),
      });
      setUsername("");
      setDisplayName("");
      setTemporaryPassword("");
      setRole("VIEWER");
      setNotice("사용자를 생성했습니다. 최초 로그인 시 비밀번호 변경이 필요합니다.");
      await load();
    } catch {
      setNotice("사용자 생성에 실패했습니다. 아이디 중복과 비밀번호 길이를 확인하세요.");
    }
  };

  const update = async (row: ManagedUser, patch: Partial<ManagedUser>) => {
    const next = { ...row, ...patch };
    try {
      await apiFetch(`/auth/users/${encodeURIComponent(row.username)}`, {
        method: "PUT",
        body: JSON.stringify({
          display_name: next.display_name,
          role: next.role,
          active: next.active,
          server_sids: next.server_sids,
        }),
      });
      setNotice(`${row.username} 사용자의 권한을 저장했습니다.`);
      await load();
    } catch {
      setNotice("사용자 권한 저장에 실패했습니다.");
    }
  };

  const resetPassword = async (usernameToReset: string) => {
    const password = resetPasswords[usernameToReset] || "";
    if (password.length < 8) {
      setNotice("임시 비밀번호는 8자 이상이어야 합니다.");
      return;
    }
    try {
      await apiFetch(`/auth/users/${encodeURIComponent(usernameToReset)}/reset-password`, {
        method: "POST",
        body: JSON.stringify({ temporary_password: password }),
      });
      setResetPasswords((current) => ({ ...current, [usernameToReset]: "" }));
      setNotice(`${usernameToReset} 사용자의 비밀번호를 초기화했습니다.`);
      await load();
    } catch {
      setNotice("비밀번호 초기화에 실패했습니다.");
    }
  };

  return (
    <section className="settings-section">
      <header className="settings-section-header">
        <div><p className="kicker">IDENTITY & ACCESS</p><h3>사용자·권한 관리</h3><p>역할과 접근 가능한 SAP PO 서버를 함께 관리합니다.</p></div>
      </header>

      <div className="role-guide">
        {(Object.keys(roleLabels) as Role[]).map((code) => <article key={code}><b>{roleLabels[code]}</b><small>{code}</small><p>{roleDescriptions[code]}</p></article>)}
      </div>

      <form className="user-create-form" onSubmit={create}>
        <label><span>사용자 ID</span><input value={username} onChange={(event) => setUsername(event.target.value.toLowerCase())} placeholder="영문 소문자 ID" /></label>
        <label><span>표시 이름</span><input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="홍길동" /></label>
        <label><span>임시 비밀번호</span><input type="password" value={temporaryPassword} onChange={(event) => setTemporaryPassword(event.target.value)} placeholder="8자 이상" /></label>
        <label><span>역할</span><select value={role} onChange={(event) => setRole(event.target.value as Role)}>{(Object.keys(roleLabels) as Role[]).map((code) => <option key={code} value={code}>{roleLabels[code]}</option>)}</select></label>
        <button className="primary-button" disabled={!username || !displayName || temporaryPassword.length < 8}>사용자 생성</button>
      </form>

      {notice && <p className="inline-notice">{notice}</p>}
      <div className="managed-user-list">
        {users.map((row) => (
          <details key={row.username}>
            <summary>
              <span><i className={`status-dot ${row.active ? "running" : "stopped"}`} /><b>{row.display_name}</b><small>{row.username}</small></span>
              <em>{roleLabels[row.role]}</em>
            </summary>
            <div className="managed-user-editor">
              <label><span>표시 이름</span><input value={row.display_name} onChange={(event) => setUsers((current) => current.map((user) => user.username === row.username ? { ...user, display_name: event.target.value } : user))} /></label>
              <label><span>역할</span><select value={row.role} onChange={(event) => setUsers((current) => current.map((user) => user.username === row.username ? { ...user, role: event.target.value as Role } : user))}>{(Object.keys(roleLabels) as Role[]).map((code) => <option key={code} value={code}>{roleLabels[code]}</option>)}</select></label>
              <label className="active-toggle"><input type="checkbox" checked={row.active} disabled={row.username === currentUsername} onChange={(event) => setUsers((current) => current.map((user) => user.username === row.username ? { ...user, active: event.target.checked } : user))} /><span>계정 활성화</span></label>
              <fieldset><legend>접근 서버 <small>미선택 시 접근 서버 없음 · admin은 전체</small></legend>{servers.map((server) => <label key={server.sid}><input type="checkbox" checked={row.server_sids.includes(server.sid)} disabled={row.role === "ADMIN"} onChange={(event) => setUsers((current) => current.map((user) => user.username === row.username ? { ...user, server_sids: event.target.checked ? [...user.server_sids, server.sid] : user.server_sids.filter((sid) => sid !== server.sid) } : user))} /><span>{server.display_name} · {server.sid}</span></label>)}</fieldset>
              <div className="user-editor-actions">
                <button className="primary-button" onClick={() => void update(row, {})}>권한 저장</button>
                <label><span>새 임시 비밀번호</span><input type="password" value={resetPasswords[row.username] || ""} onChange={(event) => setResetPasswords((current) => ({ ...current, [row.username]: event.target.value }))} placeholder="8자 이상" /></label>
                <button className="secondary-button" onClick={() => void resetPassword(row.username)}>비밀번호 초기화</button>
              </div>
            </div>
          </details>
        ))}
        {!loading && !users.length && <p className="empty-state">등록된 사용자가 없습니다.</p>}
      </div>
    </section>
  );
}
