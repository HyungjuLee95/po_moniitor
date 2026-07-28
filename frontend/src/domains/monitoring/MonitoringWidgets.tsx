import type { MonitoringSummary } from "../../core/types";
import { PanelHeader } from "../dashboard/PanelHeader";

const throughput = [38, 46, 41, 57, 52, 68, 61, 78, 72, 88, 76, 83, 65, 71, 62, 79, 86, 74, 91, 82, 69, 75, 63, 70];

export function formatLatencySeconds(milliseconds: number): string {
  return `${(milliseconds / 1000).toFixed(3)}초`;
}

export function HealthMetrics({
  summary,
  expanded,
  onToggle,
}: {
  summary: MonitoringSummary;
  expanded: "issues" | "latency" | null;
  onToggle: (value: "issues" | "latency") => void;
}) {
  return (
    <section className="metric-grid">
      <Metric label="전체 채널" value={summary.channels.total.toLocaleString()} meta={`${summary.channels.running}개 정상 운영`} accent="blue" trend="+1.8%" />
      <Metric label="오늘 메시지" value={summary.messages_today.toLocaleString()} meta={`${summary.success_rate}% 성공률`} accent="green" trend="+6.4%" />
      <Metric label="확인 필요" value={summary.channels.error.toLocaleString()} meta={`${summary.channels.stopped}개 중지`} accent="red" trend={expanded === "issues" ? "접기" : "상세 보기"} onClick={() => onToggle("issues")} expanded={expanded === "issues"} />
      <Metric label="평균 응답" value={formatLatencySeconds(summary.average_latency_ms)} meta={`최근 ${summary.latency_window_minutes}분 기준`} accent="violet" trend={expanded === "latency" ? "접기" : "지연 목록"} onClick={() => onToggle("latency")} expanded={expanded === "latency"} />
    </section>
  );
}

export function ThroughputWidget() {
  return (
    <article className="surface throughput-card span-two">
      <PanelHeader eyebrow="MESSAGE THROUGHPUT" title="24시간 처리 흐름" action="시간별" />
      <div className="throughput-chart">
        <div className="chart-scale"><span>300K</span><span>200K</span><span>100K</span><span>0</span></div>
        <div className="chart-bars">
          {throughput.map((height, index) => <i key={index} style={{ height: `${height}%` }} title={`${index}:00 · ${height * 3200}건`} />)}
        </div>
      </div>
      <div className="chart-axis"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div>
    </article>
  );
}

function Metric({ label, value, meta, accent, trend, onClick, expanded }: { label: string; value: string; meta: string; accent: string; trend: string; onClick?: () => void; expanded?: boolean }) {
  const content = (
    <>
      <div><span>{label}</span><i /></div>
      <strong>{value}</strong>
      <footer><small>{meta}</small><em>{trend}</em></footer>
    </>
  );
  if (onClick) {
    return <button className={`metric-card metric-action ${accent}`} onClick={onClick} aria-expanded={expanded}>{content}</button>;
  }
  return <article className={`metric-card ${accent}`}>{content}</article>;
}
