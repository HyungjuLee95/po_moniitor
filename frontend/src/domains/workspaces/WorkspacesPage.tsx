"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User, WorkspaceRecord } from "../../core/types";


const statusLabel = {
  planned: "계획",
  in_progress: "진행 중",
  review: "검토",
  completed: "완료",
};

export function WorkspacesPage({ user }: { user: User }) {
  const [rows, setRows] = useState<WorkspaceRecord[]>([]);
  const [taskName, setTaskName] = useState("");
  const [description, setDescription] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const canWrite = user.permissions.includes("*") || user.permissions.includes("workspaces:write");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const payload = await apiFetch<{ data: WorkspaceRecord[] }>("/workspaces");
      setRows(payload.data);
    } catch {
      setNotice("워크스페이스를 불러오지 못했습니다.");
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
    if (!taskName.trim() || !canWrite) return;
    try {
      await apiFetch("/workspaces", {
        method: "POST",
        body: JSON.stringify({
          task_name: taskName.trim(),
          description: description.trim() || null,
          progress: 0,
          target_date: targetDate || null,
        }),
      });
      setTaskName("");
      setDescription("");
      setTargetDate("");
      setNotice("새 작업공간을 만들었습니다.");
      await load();
    } catch {
      setNotice("작업공간 생성에 실패했습니다.");
    }
  };

  const advance = async (workspaceId: number) => {
    try {
      await apiFetch(`/workspaces/${workspaceId}/move-to-next-step`, { method: "POST" });
      await load();
    } catch {
      setNotice("다음 단계 이동에 실패했습니다.");
    }
  };

  const remove = async (workspaceId: number) => {
    try {
      await apiFetch(`/workspaces/${workspaceId}`, { method: "DELETE" });
      await load();
    } catch {
      setNotice("작업공간 삭제에 실패했습니다.");
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">PROJECT WORKSPACE</p>
          <h2>운영 작업 워크스페이스</h2>
          <p>담당 작업, 목표일과 진행 단계를 사용자별로 관리합니다.</p>
        </div>
      </header>
      {canWrite && (
        <form className="workspace-create" onSubmit={create}>
          <label><span>작업명</span><input value={taskName} onChange={(event) => setTaskName(event.target.value)} placeholder="새 운영 작업" /></label>
          <label><span>설명</span><input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="작업 범위와 완료 조건" /></label>
          <label><span>목표일</span><input type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} /></label>
          <button className="primary-button" disabled={!taskName.trim()}>생성</button>
        </form>
      )}
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="workspace-grid">
        {rows.map((row) => (
          <article className="workspace-card" key={row.workspace_id}>
            <header><i className={row.status} /><span>{statusLabel[row.status]}</span><small>{row.target_date || "목표일 없음"}</small></header>
            <h3>{row.task_name}</h3>
            <p>{row.description || "설명이 없습니다."}</p>
            <div className="progress-track"><i style={{ width: `${row.progress}%` }} /></div>
            <footer><b>{row.progress}%</b><span>{new Date(row.updated_at).toLocaleString("ko-KR")}</span></footer>
            {canWrite && (
              <div className="workspace-actions">
                <button onClick={() => void advance(row.workspace_id)} disabled={row.status === "completed"}>{row.status === "completed" ? "완료됨" : "다음 단계"}</button>
                <button className="danger-text" onClick={() => void remove(row.workspace_id)}>삭제</button>
              </div>
            )}
          </article>
        ))}
        {!loading && !rows.length && <p className="empty-state">아직 등록된 작업공간이 없습니다.</p>}
      </div>
    </section>
  );
}
