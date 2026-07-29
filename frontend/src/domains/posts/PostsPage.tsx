"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User } from "../../core/types";


type Post = { post_id: number; author_username: string; title: string; content: string; category: string; updated_at: string };


export function PostsPage({ user }: { user: User }) {
  const [rows, setRows] = useState<Post[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("OPERATIONS");
  const [notice, setNotice] = useState("");
  const canWrite = user.permissions.includes("*") || user.permissions.includes("posts:write");

  const load = useCallback(() => apiFetch<{ data: Post[] }>("/posts").then((payload) => setRows(payload.data)).catch(() => setNotice("게시글을 불러오지 못했습니다.")), []);
  useEffect(() => { void load(); }, [load]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await apiFetch("/posts", { method: "POST", body: JSON.stringify({ title, content, category }) });
      setTitle(""); setContent(""); setNotice("게시글을 등록했습니다."); await load();
    } catch { setNotice("게시글 등록에 실패했습니다."); }
  };

  const remove = async (postId: number) => {
    if (!window.confirm("게시글을 삭제할까요?")) return;
    try { await apiFetch(`/posts/${postId}`, { method: "DELETE" }); await load(); }
    catch { setNotice("게시글 삭제에 실패했습니다."); }
  };

  const edit = async (row: Post) => {
    const nextTitle = window.prompt("수정할 제목", row.title);
    if (nextTitle === null) return;
    const nextContent = window.prompt("수정할 본문", row.content);
    if (nextContent === null) return;
    try {
      await apiFetch(`/posts/${row.post_id}`, {
        method: "PUT",
        body: JSON.stringify({ title: nextTitle, content: nextContent, category: row.category }),
      });
      setNotice("게시글을 수정했습니다."); await load();
    } catch { setNotice("게시글 수정에 실패했습니다."); }
  };

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">KNOWLEDGE BASE</p><h2>운영 지식 게시글</h2><p>점검 절차와 장애 해결 경험을 팀과 공유합니다.</p></div></header>
      {notice && <p className="inline-notice">{notice}</p>}
      {canWrite && <form className="post-compose" onSubmit={submit}><div><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="제목" required /><select value={category} onChange={(event) => setCategory(event.target.value)}><option>OPERATIONS</option><option>INCIDENT</option><option>MANUAL</option></select></div><textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="운영 지식을 입력하세요." required /><button className="primary-button">등록</button></form>}
      <div className="post-list">{rows.map((row) => <article className="detail-card" key={row.post_id}><p className="kicker">{row.category}</p><h3>{row.title}</h3><p className="post-meta">{row.author_username} · {new Date(row.updated_at).toLocaleString("ko-KR")}</p><p className="post-content">{row.content}</p>{(user.role === "ADMIN" || row.author_username === user.username) && <div className="control-actions"><button className="row-action" onClick={() => void edit(row)}>수정</button><button className="row-action" onClick={() => void remove(row.post_id)}>삭제</button></div>}</article>)}{!rows.length && <p className="empty-state">등록된 게시글이 없습니다.</p>}</div>
    </section>
  );
}
