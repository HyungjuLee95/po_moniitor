"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";


type CertificateStatus = "EXPIRED" | "EXPIRING" | "VALID" | "UNKNOWN";

type CertificateRow = {
  sid: string;
  view: string;
  alias: string;
  kind: "PRIVATE_KEY" | "TRUSTED_CERTIFICATE";
  subject_dn: string;
  issuer_dn: string;
  not_before: string | null;
  not_after: string | null;
  not_before_raw: string;
  not_after_raw: string;
  serial_number: string;
  signature_algorithm: string;
  days_remaining: number | null;
  status: CertificateStatus;
  sources: string[];
};

type CertificateMeta = {
  sid: string;
  count: number;
  views: string[];
  warning_days: number;
  expiry_available: boolean;
  summary: Record<"expired" | "expiring" | "valid" | "unknown", number>;
  notice: string;
  services: Record<string, string>;
  source: string;
};

const statusLabel: Record<CertificateStatus, string> = {
  EXPIRED: "만료됨",
  EXPIRING: "만료 임박",
  VALID: "정상",
  UNKNOWN: "만료일 미확인",
};

function displayDate(value: string | null, raw: string): string {
  if (value && /^\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10);
  return raw || "—";
}

function csvCell(value: unknown): string {
  const original = String(value ?? "");
  const hardened = /^[=+\-@]/.test(original) ? `'${original}` : original;
  return `"${hardened.replaceAll('"', '""')}"`;
}

export function CertificatesPage({ sid }: { sid: string }) {
  const [rows, setRows] = useState<CertificateRow[]>([]);
  const [meta, setMeta] = useState<CertificateMeta | null>(null);
  const [warningDays, setWarningDays] = useState(30);
  const [view, setView] = useState("ALL");
  const [status, setStatus] = useState<CertificateStatus | "ALL">("ALL");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<{ data: CertificateRow[]; meta: CertificateMeta }>(
        `/certificates?sid=${encodeURIComponent(sid)}&warning_days=${warningDays}`,
        { timeoutMs: 75_000 },
      );
      setRows(payload.data);
      setMeta(payload.meta);
    } catch {
      setRows([]);
      setMeta(null);
      setError("인증서 정보를 조회하지 못했습니다. SAP PO 키스토어 권한과 서비스 상태를 확인하세요.");
    } finally {
      setLoading(false);
    }
  }, [sid, warningDays]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const visibleRows = useMemo(() => {
    const term = query.trim().toLowerCase();
    const order: Record<CertificateStatus, number> = {
      EXPIRED: 0,
      EXPIRING: 1,
      UNKNOWN: 2,
      VALID: 3,
    };
    return rows
      .filter((row) => view === "ALL" || row.view === view)
      .filter((row) => status === "ALL" || row.status === status)
      .filter((row) => !term || [row.view, row.alias, row.subject_dn, row.issuer_dn, row.serial_number]
        .some((value) => value.toLowerCase().includes(term)))
      .sort((left, right) => order[left.status] - order[right.status]
        || (left.days_remaining ?? Number.MAX_SAFE_INTEGER) - (right.days_remaining ?? Number.MAX_SAFE_INTEGER)
        || left.alias.localeCompare(right.alias));
  }, [query, rows, status, view]);

  const exportCsv = () => {
    const header = ["SID", "View", "Alias", "종류", "Subject DN", "Issuer DN", "시작일", "만료일", "D-day", "상태", "시리얼", "서명 알고리즘"];
    const lines = visibleRows.map((row) => [
      row.sid,
      row.view,
      row.alias,
      row.kind,
      row.subject_dn,
      row.issuer_dn,
      displayDate(row.not_before, row.not_before_raw),
      displayDate(row.not_after, row.not_after_raw),
      row.days_remaining ?? "",
      statusLabel[row.status],
      row.serial_number,
      row.signature_algorithm,
    ].map(csvCell).join(","));
    const blob = new Blob(["\ufeff", [header.map(csvCell).join(","), ...lines].join("\r\n")], { type: "text/csv;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `PO_Certificates_${sid}.csv`;
    anchor.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <section className="feature-page certificate-page">
      <header className="feature-header">
        <div>
          <p className="kicker">CERTIFICATE MONITORING</p>
          <h2>인증서 만료 현황</h2>
          <p>SAP PO AS Java 키스토어의 View·Alias·인증서 기간을 조회합니다.</p>
        </div>
        <div className="control-actions">
          <button onClick={exportCsv} disabled={!visibleRows.length}>CSV 내보내기</button>
          <button onClick={() => void load()} disabled={loading}>{loading ? "조회 중…" : "새로고침"}</button>
        </div>
      </header>

      {meta?.notice && <p className="inline-notice certificate-notice">{meta.notice}</p>}
      {error && <p className="form-error">{error}</p>}

      <section className="certificate-summary" aria-label="인증서 상태 요약">
        <article className="expired"><span>만료</span><strong>{meta?.summary.expired ?? 0}</strong><small>즉시 교체 필요</small></article>
        <article className="expiring"><span>{warningDays}일 이내</span><strong>{meta?.summary.expiring ?? 0}</strong><small>갱신 일정 확인</small></article>
        <article className="valid"><span>정상</span><strong>{meta?.summary.valid ?? 0}</strong><small>기준일 초과</small></article>
        <article className="unknown"><span>미확인</span><strong>{meta?.summary.unknown ?? 0}</strong><small>만료일 서비스 미제공 포함</small></article>
      </section>

      <section className="feature-toolbar certificate-toolbar">
        <label className="search-field"><span>검색</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="View, Alias, Subject, Issuer, Serial" /></label>
        <label><span>키스토어 View</span><select value={view} onChange={(event) => setView(event.target.value)}><option value="ALL">전체</option>{meta?.views.map((item) => <option value={item} key={item}>{item}</option>)}</select></label>
        <label><span>상태</span><select value={status} onChange={(event) => setStatus(event.target.value as CertificateStatus | "ALL")}><option value="ALL">전체</option><option value="EXPIRED">만료됨</option><option value="EXPIRING">만료 임박</option><option value="VALID">정상</option><option value="UNKNOWN">미확인</option></select></label>
        <label><span>임박 기준</span><select value={warningDays} onChange={(event) => setWarningDays(Number(event.target.value))}>{[7, 14, 30, 60, 90, 180, 365].map((days) => <option value={days} key={days}>{days}일</option>)}</select></label>
      </section>

      <section className="table-card certificate-table">
        <header className="table-caption"><b>키스토어 인증서</b><span>{visibleRows.length.toLocaleString()} / {meta?.count.toLocaleString() ?? 0} entries</span></header>
        <div className="data-table">
          <div className="data-row data-head"><span>View / Alias</span><span>종류</span><span>Subject</span><span>만료일</span><span>D-day</span><span>상태</span></div>
          {loading && <p className="empty-state">SAP PO 키스토어를 조회하고 있습니다.</p>}
          {!loading && !visibleRows.length && <p className="empty-state">조건에 맞는 인증서가 없습니다.</p>}
          {!loading && visibleRows.map((row, index) => (
            <details className={`certificate-row ${row.status.toLowerCase()}`} key={`${row.view}|${row.alias}|${index}`}>
              <summary className="data-row">
                <span><b>{row.alias || "Alias 없음"}</b><small>{row.view || "View 없음"}</small></span>
                <span>{row.kind === "PRIVATE_KEY" ? "Private Key" : "Trusted Certificate"}</span>
                <span>{row.subject_dn || "—"}</span>
                <span>{displayDate(row.not_after, row.not_after_raw)}</span>
                <span>{row.days_remaining === null ? "—" : row.days_remaining === 0 ? "D-day" : row.days_remaining > 0 ? `D-${row.days_remaining}` : `D+${Math.abs(row.days_remaining)}`}</span>
                <span><i className={`certificate-status ${row.status.toLowerCase()}`}>{statusLabel[row.status]}</i></span>
              </summary>
              <div className="certificate-detail">
                <div><b>Issuer DN</b><span>{row.issuer_dn || "—"}</span></div>
                <div><b>유효 기간</b><span>{displayDate(row.not_before, row.not_before_raw)} → {displayDate(row.not_after, row.not_after_raw)}</span></div>
                <div><b>Serial Number</b><span>{row.serial_number || "—"}</span></div>
                <div><b>Signature</b><span>{row.signature_algorithm || "—"}</span></div>
                <div><b>원본 서비스</b><span>{row.sources.join(", ") || "—"}</span></div>
              </div>
            </details>
          ))}
        </div>
      </section>
    </section>
  );
}
