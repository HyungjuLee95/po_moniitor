"use client";

import { useEffect, useState } from "react";

import { apiFetch, apiRequest } from "../../core/api";
import type { User } from "../../core/types";


type HrdRow = {
  sid: string;
  component_id: string;
  channel_id: string;
  if_id: string;
  dist_if_id: string;
  company_cd: string[];
  dist_cnt: number;
  table_name: string | null;
  batch_tm: string | null;
  match_type: string;
};

function uniqueSorted(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right));
}

function FilterChecklist({
  title,
  options,
  selected,
  onToggle,
  onSelectAll,
  onClear,
  disabled,
  help,
}: {
  title: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  onSelectAll: () => void;
  onClear: () => void;
  disabled: boolean;
  help: string;
}) {
  const allSelected = options.length > 0 && selected.length === options.length;
  return (
    <fieldset className="hrd-filter-group">
      <legend>{title}</legend>
      <div className="hrd-filter-meta">
        <span>{allSelected ? "전체 선택됨" : `${selected.length}/${options.length}개 선택`}</span>
        <button
          type="button"
          onClick={allSelected ? onClear : onSelectAll}
          disabled={!options.length || disabled}
        >
          {allSelected ? "전체 해제" : "전체 선택"}
        </button>
      </div>
      <div className="hrd-check-list">
        {options.map((option) => (
          <label className="hrd-check-option" key={option}>
            <input
              type="checkbox"
              checked={selected.includes(option)}
              disabled={disabled}
              onChange={() => onToggle(option)}
            />
            <span>{option}</span>
          </label>
        ))}
        {!options.length && <p>조회 결과에서 선택 항목이 없습니다.</p>}
      </div>
      <small>{help}</small>
    </fieldset>
  );
}

export function HrdPage({ sid, user, testMode = false }: { sid: string; user: User; testMode?: boolean }) {
  const [query, setQuery] = useState("");
  const [companyCodes, setCompanyCodes] = useState<string[]>([]);
  const [tableNames, setTableNames] = useState<string[]>([]);
  const [companyOptions, setCompanyOptions] = useState<string[]>([]);
  const [tableOptions, setTableOptions] = useState<string[]>([]);
  const [rows, setRows] = useState<HrdRow[]>([]);
  const [selectedIfId, setSelectedIfId] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const canTest = user.permissions.includes("*") || user.permissions.includes("hrd:test");

  const params = () => {
    const search = new URLSearchParams({ sid });
    if (query.trim()) search.set("search_ifid", query.trim());
    if (companyCodes.length !== companyOptions.length) {
      companyCodes.forEach((value) => search.append("company_codes", value));
    }
    if (tableNames.length !== tableOptions.length) {
      tableNames.forEach((value) => search.append("table_names", value));
    }
    return search;
  };

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setLoading(true);
      setCompanyCodes([]);
      setTableNames([]);
      const initial = new URLSearchParams({ sid });
      apiFetch<{ data: HrdRow[] }>(`/hrd/interfaces?${initial}`)
        .then((payload) => {
          if (cancelled) return;
          setRows(payload.data);
          const nextCompanyOptions = uniqueSorted(payload.data.flatMap((row) => row.company_cd));
          const nextTableOptions = uniqueSorted(payload.data.map((row) => row.table_name));
          setCompanyOptions(nextCompanyOptions);
          setTableOptions(nextTableOptions);
          setCompanyCodes(nextCompanyOptions);
          setTableNames(nextTableOptions);
          setNotice("");
        })
        .catch(() => {
          if (cancelled) return;
          setRows([]);
          setCompanyOptions([]);
          setTableOptions([]);
          setNotice("HRD 필터 목록과 인터페이스를 불러오지 못했습니다.");
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [sid]);

  const search = async () => {
    if ((companyOptions.length && !companyCodes.length) || (tableOptions.length && !tableNames.length)) {
      setRows([]);
      setNotice("법인코드와 테이블명은 각각 하나 이상 선택해 주세요.");
      return;
    }
    setLoading(true);
    setNotice("");
    try {
      const payload = await apiFetch<{ data: HrdRow[] }>(`/hrd/interfaces?${params()}`);
      setRows(payload.data);
      setNotice(`${payload.data.length}개 HRD 인터페이스를 조회했습니다.`);
    } catch {
      setRows([]);
      setNotice("HRD 인터페이스를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const toggleCompany = (value: string) => {
    setCompanyCodes((current) => current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value]);
  };

  const toggleTable = (value: string) => {
    setTableNames((current) => current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value]);
  };

  const download = async () => {
    if ((companyOptions.length && !companyCodes.length) || (tableOptions.length && !tableNames.length)) {
      setNotice("Excel 다운로드 전에 법인코드와 테이블명을 각각 하나 이상 선택해 주세요.");
      return;
    }
    try {
      const response = await apiRequest(`/hrd/interfaces/excel?${params()}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `HRD_Interfaces_${sid}.xlsx`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setNotice("Excel 다운로드에 실패했습니다.");
    }
  };

  const sendTest = async () => {
    if (!selectedIfId || !canTest) return;
    if (!window.confirm(`${sid} 서버로 ${selectedIfId} 테스트 메시지를 전송할까요?`)) return;
    try {
      await apiFetch("/hrd/test-message", {
        method: "POST",
        body: JSON.stringify({ sid, if_id: selectedIfId }),
      });
      setNotice("테스트 메시지 전송 요청이 완료되었습니다.");
    } catch {
      setNotice("테스트 메시지 전송에 실패했습니다.");
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div><p className="kicker">{testMode ? "HRD TEST MESSAGE" : "HRD INTERFACE LOOKUP"}</p><h2>{testMode ? "HRD 테스트 메시지" : "HRD 인터페이스 조회"}</h2><p>{testMode ? "대상 I/F를 조회·선택한 뒤 현재 서버로 테스트 메시지를 전송합니다." : "분배 채널, 테이블·법인코드와 배치 스케줄을 조회합니다."}</p></div>
        {!testMode && <button className="secondary-button" onClick={() => void download()}>Excel 다운로드</button>}
      </header>
      <div className="feature-toolbar hrd-search-toolbar">
        <div className="hrd-search-row">
          <label className="search-field"><span>I/F ID</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="HRD I/F 검색" /></label>
          <button className="primary-button" onClick={() => void search()} disabled={loading}>{loading ? "조회 중…" : "조회"}</button>
        </div>
        <div className="hrd-filter-panel">
          <FilterChecklist
            title={`법인코드 (${companyOptions.length})`}
            options={companyOptions}
            selected={companyCodes}
            onToggle={toggleCompany}
            onSelectAll={() => setCompanyCodes(companyOptions)}
            onClear={() => setCompanyCodes([])}
            disabled={loading}
            help="선택한 법인코드 조합과 SQL IN 목록이 정확히 일치하는 인터페이스를 조회합니다."
          />
          <FilterChecklist
            title={`테이블명 (${tableOptions.length})`}
            options={tableOptions}
            selected={tableNames}
            onToggle={toggleTable}
            onSelectAll={() => setTableNames(tableOptions)}
            onClear={() => setTableNames([])}
            disabled={loading}
            help="여러 테이블을 선택하면 선택한 테이블 중 하나에 해당하는 인터페이스를 조회합니다."
          />
        </div>
      </div>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="table-card">
        <div className="table-caption"><b>{rows.length} interfaces</b><span>{sid}</span></div>
        <div className="data-table hrd-table">
          <div className="data-row data-head"><span>I/F ID</span><span>DIST 채널</span><span>Table</span><span>Company</span><span>Batch</span><span /></div>
          {rows.map((row) => (
            <div className="data-row" key={`${row.component_id}|${row.channel_id}`}>
              <span><b>{row.if_id}</b><small>{row.match_type}</small></span>
              <span>{row.dist_if_id}<small>{row.dist_cnt} targets</small></span>
              <span>{row.table_name || "—"}</span>
              <span>{row.company_cd.join(", ") || "—"}</span>
              <span>{row.batch_tm || "수동/미정의"}</span>
              <span>{testMode && <button className="row-action" onClick={() => setSelectedIfId(row.if_id)}>테스트 선택</button>}</span>
            </div>
          ))}
          {!loading && !rows.length && <p className="empty-state">조회 조건을 입력하고 HRD 인터페이스를 검색하세요.</p>}
        </div>
      </div>
      {testMode && <section className="settings-section compact-action">
        <div><p className="kicker">TEST MESSAGE</p><h3>{selectedIfId || "I/F를 선택하세요"}</h3><p>선택 서버의 HRD 테스트 경로로 최소 테스트 메시지를 전송합니다.</p></div>
        <button className="primary-button" disabled={!selectedIfId || !canTest} onClick={() => void sendTest()}>테스트 전송</button>
      </section>}
    </section>
  );
}
