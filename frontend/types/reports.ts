export type ReportKey = "sales_by_restaurant" | "popular_dishes" | "courier_performance";

/** How to show a value: money is kopiyky, minutes are whole minutes, percent is 0–100. */
export type ReportColumnKind = "text" | "count" | "money" | "minutes" | "percent";

export interface ReportInfo {
  key: ReportKey;
  title: string;
}

export interface ReportColumn {
  key: string;
  label: string;
  kind: ReportColumnKind;
}

export type ReportValue = string | number | null;

export interface Report {
  key: ReportKey;
  title: string;
  date_from: string;
  date_to: string;
  columns: ReportColumn[];
  rows: Record<string, ReportValue>[];
  totals: Record<string, ReportValue> | null;
}
