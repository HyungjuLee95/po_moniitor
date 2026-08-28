"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import type { ManagedUser, PoServer, Role } from "../../core/types";

const roleLabels: Record<Role, string> = {
  ADMIN: "Administrator",
  OPERATOR: "관리자",
  VIEWER: "일반",
};

const roleDescriptions: Record<Role, string> = {
  ADMIN: "시스템에 하나만 존재하며 사용자·환경 전체를 관리합니다.",
  OPERATOR: "모니터링 조회, 장애 처리와 채널 운영을 수행합니다.",
  VIEWER: "허용된 서버의 현황과 메시지를 조회합니다.",
};

const assignableRoles: Role[] = ["OPERATOR", "VIEWER"];
type ResetRequest = { request_id: number; username: string; requested_at: string; expires_at: string };

export function UserManagementPanel({ servers }: { servers: PoServer[] }) {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [resetPasswords, setResetPasswords] = useState<Record<string, string>>({});
  const [resetRequests, setResetRequests] = useState<ResetRequest[]>([]);
  const [issuedToken, setIssuedToken] = useState("");

  const pendingUsers = useMemo(() => users.filter((row) => !row.active), [users]);
  const activeUsers = useMemo(() => users.filter((row) => row.active), [users]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [userPayload, resetPayload] = await Promise.all([
        apiFetch<{ data: ManagedUser[] }>("/auth/users"),
        apiFetch<{ data: ResetRequest[] }>("/auth/password-reset-requests"),
      ]);
      setUsers(userPayload.data);
      setResetRequests(resetPayload.data);
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

  const issueToken = async (requestId: number) => {
    try {
      const payload = await apiFetch<{ data: { token: string } }>(`/auth/password-reset-requests/${requestId}/issue-token`, { method: "POST" });
      setIssuedToken(payload.data.token);
      setNotice("30분 유효 1회 토큰을 발급했습니다. 안전한 내부 수단으로 사용자에게 전달하세요.");
    } catch {
      setNotice("비밀번호 재설정 토큰 발급에 실패했습니다.");
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
      setNotice(!row.active && next.active ? `${row.display_name} 사용자의 가입을 승인했습니다.` : `${row.display_name} 사용자의 권한을 저장했습니다.`);
      await load();
    } catch {
      setNotice("사용자 권한 저장에 실패했습니다. 역할과 접근 서버를 확인하세요.");
    }
  };

  const updateLocal = (username: string, patch: Partial<ManagedUser>) => {
    setUsers((current) => current.map((user) => user.username === username ? { ...user, ...patch } : user));
  };

  const toggleServer = (row: ManagedUser, sid: string, checked: boolean) => {
    updateLocal(row.username, {
      server_sids: checked
        ? [...row.server_sids, sid]
        : row.server_sids.filter((serverSid) => serverSid !== sid),
    });
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

  const userEditor = (row: ManagedUser) => {
    const isAdministrator = row.role === "ADMIN";
    return (
      <details key={row.username} open={!row.active} className={!row.active ? "pending-user" : ""}>
        <summary>
          <span><i className={`status-dot ${row.active ? "running" : "stopped"}`} /><b>{row.display_name}</b><small>{row.username}</small></span>
          <em className={!row.active ? "pending" : ""}>{!row.active ? "승인 대기" : roleLabels[row.role]}</em>
        </summary>
        <div className="managed-user-editor">
          <label><span>표시 이름</span><input value={row.display_name} onChange={(event) => updateLocal(row.username, { display_name: event.target.value })} /></label>
          <label><span>역할</span><select value={row.role} disabled={isAdministrator} onChange={(event) => updateLocal(row.username, { role: event.target.value as Role })}>{isAdministrator ? <option value="ADMIN">Administrator</option> : assignableRoles.map((code) => <option key={code} value={code}>{roleLabels[code]}</option>)}</select></label>
          <label className="active-toggle"><input type="checkbox" checked={row.active} disabled readOnly /><span>{isAdministrator ? "고정 활성화" : row.active ? "활성 계정" : "승인 전"}</span></label>
          <fieldset>
            <legend>접근 서버 <small>{isAdministrator ? "Administrator는 전체 서버" : "하나 이상 선택 후 승인"}</small></legend>
            {isAdministrator
              ? <p className="administrator-scope">등록된 모든 서버에 접근합니다.</p>
              : servers.map((server) => <label key={server.sid}><input type="checkbox" checked={row.server_sids.includes(server.sid)} onChange={(event) => toggleServer(row, server.sid, event.target.checked)} /><span>{server.display_name} · {server.sid}</span></label>)}
          </fieldset>
          <div className="user-editor-actions">
            {!isAdministrator && <button className="primary-button" disabled={!row.active && row.server_sids.length === 0} onClick={() => void update(row, row.active ? {} : { active: true })}>{row.active ? "권한 저장" : "가입 승인"}</button>}
            {!isAdministrator && row.active && <button className="secondary-button" onClick={() => void update(row, { active: false })}>계정 비활성화</button>}
            <label><span>새 임시 비밀번호</span><input type="password" value={resetPasswords[row.username] || ""} onChange={(event) => setResetPasswords((current) => ({ ...current, [row.username]: event.target.value }))} placeholder="8자 이상" /></label>
            <button className="secondary-button" onClick={() => void resetPassword(row.username)}>비밀번호 초기화</button>
          </div>
        </div>
      </details>
    );
  };

  return (
    <section className="settings-section">
      <header className="settings-section-header">
        <div><p className="kicker">IDENTITY & ACCESS</p><h3>가입 승인·권한 관리</h3><p>사용자는 로그인 화면에서 가입하고, Administrator가 역할과 접근 서버를 승인합니다.</p></div>
      </header>

      <div className="access-overview">
        <article><span>Administrator</span><b>1</b><small>고정 관리자</small></article>
        <article className={pendingUsers.length ? "attention" : ""}><span>승인 대기</span><b>{pendingUsers.length}</b><small>가입 신청</small></article>
        <article><span>활성 계정</span><b>{activeUsers.length}</b><small>Administrator 포함</small></article>
      </div>

      <div className="role-guide">
        {(Object.keys(roleLabels) as Role[]).map((code) => <article key={code}><b>{roleLabels[code]}</b><small>{code}</small><p>{roleDescriptions[code]}</p></article>)}
      </div>

      {notice && <p className="inline-notice">{notice}</p>}
      {issuedToken && <div className="reset-token-box"><b>1회 재설정 토큰</b><code>{issuedToken}</code><button className="row-action" onClick={() => void navigator.clipboard.writeText(issuedToken)}>복사</button></div>}
      {resetRequests.length > 0 && <section className="approval-section"><header><b>비밀번호 재설정 요청</b><span>{resetRequests.length}건</span></header><div className="reset-request-list">{resetRequests.map((request) => <div key={request.request_id}><span><b>{request.username}</b><small>{new Date(request.requested_at).toLocaleString("ko-KR")}</small></span><button className="secondary-button" onClick={() => void issueToken(request.request_id)}>1회 토큰 발급</button></div>)}</div></section>}

      <section className="approval-section">
        <header><div><b>가입 승인 대기</b><small>역할과 서버를 지정한 뒤 승인하세요.</small></div><span>{pendingUsers.length}건</span></header>
        <div className="managed-user-list">
          {pendingUsers.map(userEditor)}
          {!loading && !pendingUsers.length && <p className="empty-state">대기 중인 가입 신청이 없습니다.</p>}
        </div>
      </section>

      <section className="approval-section">
        <header><div><b>활성 사용자</b><small>권한 변경과 비밀번호 초기화를 관리합니다.</small></div><span>{activeUsers.length}명</span></header>
        <div className="managed-user-list">
          {activeUsers.map(userEditor)}
          {!loading && !activeUsers.length && <p className="empty-state">활성 사용자가 없습니다.</p>}
        </div>
      </section>
    </section>
  );
}
