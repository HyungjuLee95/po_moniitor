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
      setAnswer("LLM JSON API 호출에 실패했습니다. 백엔드의 LLM_API_URL 설정과 대상 API 상태를 확인해 주세요.");
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
          <p>{answer || "LLM JSON API의 분석 결과가 이 영역에 표시됩니다."}</p>
        </div>
      </section>
    </div>
  );
}
