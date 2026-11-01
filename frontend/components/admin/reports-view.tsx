"use client";

import { Download } from "lucide-react";
import { useState } from "react";
import useSWR from "swr";

import { api, type ApiError } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { useAsyncAction } from "@/lib/use-async-action";
import type { Report, ReportColumn, ReportColumnKind, ReportInfo, ReportKey, ReportValue } from "@/types/reports";

/** What each report counts, shown under the tabs. */
const DESCRIPTIONS: Record<ReportKey, string> = {
  sales_by_restaurant: "Orders placed in the period. Revenue and discounts count delivered orders only.",
  popular_dishes: "Dishes from delivered orders placed in the period, by portions sold.",
  courier_performance: "Delivered orders by courier. On time means delivered within the ETA promised at checkout.",
};

const PRESETS = [
  { label: "7 days", days: 7 },
  { label: "30 days", days: 30 },
  { label: "90 days", days: 90 },
] as const;

/** Local calendar day as the API expects it ("2026-10-31"). */
function isoDay(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function lastDays(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - (days - 1));
  return { from: isoDay(from), to: isoDay(to) };
}

function formatCell(kind: ReportColumnKind, value: ReportValue | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  switch (kind) {
    case "money":
      return formatPrice(value);
    case "minutes":
      return `${value} min`;
    case "percent":
      return `${value}%`;
    default:
      return String(value);
  }
}

const isNumeric = (column: ReportColumn) => column.kind !== "text";

export function ReportsView() {
  const [reportKey, setReportKey] = useState<ReportKey>("sales_by_restaurant");
  const [period, setPeriod] = useState(() => lastDays(90));
  const download = useAsyncAction();

  const { data: reports } = useSWR<{ items: ReportInfo[] }>("/admin/reports");
  const query = new URLSearchParams({ date_from: period.from, date_to: period.to });
  const ready = period.from !== "" && period.to !== "";
  const { data: report, error, isLoading } = useSWR<Report, ApiError>(
    ready ? `/admin/reports/${reportKey}?${query}` : null,
    { keepPreviousData: true },
  );

  async function downloadCsv() {
    const blob = await download.run(() => api.download(`/admin/reports/${reportKey}?${query}&format=csv`));
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${reportKey}_${period.from}_${period.to}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const filterClass = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-accent";
  const activePreset = PRESETS.find((p) => {
    const range = lastDays(p.days);
    return range.from === period.from && range.to === period.to;
  });
  // A stale table from the previous request is kept while the next one loads, but not on error.
  const shown = error ? undefined : report;
  const totals = shown?.totals;

  return (
    <div>
      <h1 className="font-serif text-3xl text-ink">Reports</h1>

      <div role="group" aria-label="Report" className="mt-5 flex flex-wrap gap-1 border-b border-line">
        {(reports?.items ?? []).map((r) => (
          <button
            key={r.key}
            type="button"
            aria-pressed={r.key === reportKey}
            onClick={() => setReportKey(r.key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition ${
              r.key === reportKey ? "border-accent text-ink" : "border-transparent text-muted-ink hover:text-ink"
            }`}
          >
            {r.title}
          </button>
        ))}
      </div>
      <p className="mt-3 text-sm text-muted-ink">{DESCRIPTIONS[reportKey]}</p>

      <div className="mt-5 flex flex-wrap items-end gap-3">
        <div role="group" aria-label="Quick periods" className="flex gap-1">
          {PRESETS.map((p) => (
            <button
              key={p.days}
              type="button"
              aria-pressed={activePreset === p}
              onClick={() => setPeriod(lastDays(p.days))}
              className={`rounded-full px-3 py-2 text-sm font-medium transition ${
                activePreset === p ? "bg-ink text-background" : "border border-line text-ink hover:bg-surface"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <label className="text-xs text-muted-ink">
          From
          <input
            type="date"
            value={period.from}
            max={period.to || undefined}
            onChange={(e) => setPeriod({ ...period, from: e.target.value })}
            className={`mt-1 block ${filterClass}`}
          />
        </label>
        <label className="text-xs text-muted-ink">
          To
          <input
            type="date"
            value={period.to}
            min={period.from || undefined}
            onChange={(e) => setPeriod({ ...period, to: e.target.value })}
            className={`mt-1 block ${filterClass}`}
          />
        </label>
        <button
          type="button"
          onClick={() => void downloadCsv()}
          disabled={!shown || shown.rows.length === 0 || download.pending}
          className="ml-auto inline-flex items-center gap-2 rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
        >
          <Download aria-hidden className="h-4 w-4" />
          {download.pending ? "Preparing…" : "Download CSV"}
        </button>
      </div>
      {download.error && (
        <p role="alert" className="mt-2 text-sm text-accent-strong">
          {download.error}
        </p>
      )}

      {!ready ? (
        <p className="mt-6 text-sm text-muted-ink">Pick both dates to see the report.</p>
      ) : error ? (
        <p role="alert" className="mt-6 text-sm text-accent-strong">
          {error.details[0]?.message ?? error.message}
        </p>
      ) : !shown ? (
        <div className="mt-6 h-64 animate-pulse rounded-xl bg-surface" aria-busy />
      ) : shown.rows.length === 0 ? (
        <p className="mt-6 rounded-xl border border-dashed border-line px-5 py-10 text-center text-sm text-muted-ink">
          Nothing to report for these dates. Try a longer period.
        </p>
      ) : (
        <div
          className={`mt-5 overflow-x-auto rounded-xl border border-line transition-opacity ${isLoading ? "opacity-60" : ""}`}
          aria-busy={isLoading}
        >
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="bg-surface text-xs uppercase tracking-wider text-muted-ink">
              <tr>
                {shown.columns.map((c) => (
                  <th key={c.key} scope="col" className={`px-4 py-2.5 font-medium ${isNumeric(c) ? "text-right" : ""}`}>
                    {c.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-card">
              {shown.rows.map((row, i) => (
                <tr key={i} className="hover:bg-surface/50">
                  {shown.columns.map((c, j) => (
                    <td
                      key={c.key}
                      className={`px-4 py-2.5 ${isNumeric(c) ? "text-right tabular-nums" : ""} ${j === 0 ? "font-medium text-ink" : ""}`}
                    >
                      {formatCell(c.kind, row[c.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
            {totals && (
              <tfoot className="border-t-2 border-line bg-surface font-semibold text-ink">
                <tr>
                  {shown.columns.map((c, j) => (
                    <td key={c.key} className={`px-4 py-2.5 ${isNumeric(c) ? "text-right tabular-nums" : ""}`}>
                      {j === 0 ? "Total" : c.key in totals ? formatCell(c.kind, totals[c.key]) : ""}
                    </td>
                  ))}
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      )}
    </div>
  );
}
