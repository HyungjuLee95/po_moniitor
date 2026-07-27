"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "../../core/api";
import type { AlertItem } from "../alerts/types";

export function LlmSearchPanel({ alert, onClose }: { alert: AlertItem; onClose: () => void }) {
  const [question, setQuestion] = useState(`${alert.title}의 가능한 원인과 확인 순서를 알려줘`);
  const [answer, setAnswer] = useState("");
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    try {
      const payload = await apiFetch<{ data: { answer: string } }>("/llm-search/analyze", {
        method: "POST",
        body: JSON.stringify({ alert_id: alert.id, question, context: alert }),
      });
      setAnswer(payload.data.answer);
    } catch {
      setAnswer("LLM 연결 전 준비 화면입니다. 실제 연동 시 장애 문맥, 운영 매뉴얼, 과거 ERROR.md 기록을 함께 검색해 원인과 확인 순서를 제안합니다.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="llm-panel" role="dialog" aria-modal="true" aria-labelledby="llm-title" onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div>
            <p className="kicker">AI TROUBLESHOOTING</p>
            <h2 id="llm-title">오류 원인 검색</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="닫기">×</button>
        </header>
        <div className="llm-context">
          <span className={`severity ${alert.severity}`}>{alert.severity}</span>
          <div><b>{alert.title}</b><small>{alert.sid} · {alert.domain} · {alert.id}</small></div>
        </div>
        <form onSubmit={submit}>
          <label htmlFor="llm-question">검색 질문</label>
          <textarea id="llm-question" value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} />
          <button className="primary-button" type="submit" disabled={pending}>{pending ? "관련 문서 탐색 중…" : "LLM으로 분석하기"}</button>
        </form>
        <div className={`llm-answer ${answer ? "ready" : ""}`}>
          <p className="kicker">RESPONSE PREVIEW</p>
          <p>{answer || "분석 결과가 이 영역에 표시됩니다. 1차 버전은 연동 계약과 화면 형태만 제공합니다."}</p>
        </div>
      </section>
    </div>
  );
}
