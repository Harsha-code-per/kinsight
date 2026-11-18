"use client";

import { useState } from "react";
import { Brand, LangSwitch } from "@/components/PublicChrome";
import { PageHeader } from "@/components/ui";
import { useI18n } from "@/lib/i18n";
import { compareReports, parseReport } from "@/lib/report-compare";
import ComparisonView from "./ComparisonView";
import ReportAttachment from "./ReportAttachment";

const PARTNERS = ["first", "second"] as const;
type Partner = (typeof PARTNERS)[number];
type Draft = { text: string; review: "manual" | "pending" | "verified" };
const EMPTY_DRAFT: Draft = { text: "", review: "manual" };
const EMPTY_REPORTS = { first: EMPTY_DRAFT, second: EMPTY_DRAFT };

export default function ReportComparison() {
  const { t } = useI18n();
  const [drafts, setDrafts] = useState(EMPTY_REPORTS);
  const [parsed, setParsed] = useState<{ first: ReturnType<typeof parseReport>; second: ReturnType<typeof parseReport> }>();
  const [reset, setReset] = useState(0);
  const requiresReview = PARTNERS.some((side) => drafts[side].review === "pending");
  const comparison = parsed?.first.rows && parsed.second.rows ? compareReports(parsed.first.rows, parsed.second.rows) : undefined;

  function edit(side: Partner, draft: Draft) {
    setParsed(undefined);
    setDrafts((previous) => ({ ...previous, [side]: draft }));
  }

  return <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8">
    <header className="flex flex-wrap items-center justify-between gap-3">
      <Brand />
      <LangSwitch />
    </header>
    <PageHeader title={t("reportCompare.title")} lead={t("reportCompare.lead")} />
    <p className="note">{t("reportCompare.privacy")}</p>
    <form className="space-y-4" onSubmit={(event) => {
      event.preventDefault();
      if (!requiresReview) setParsed({ first: parseReport(drafts.first.text), second: parseReport(drafts.second.text) });
    }}>
      <div className="grid gap-4 md:grid-cols-2">
        {PARTNERS.map((side) => {
          const draft = drafts[side];
          const error = parsed?.[side];
          return <div className="card space-y-3" key={side}>
            <label htmlFor={`report-${side}`} className="block font-semibold">{t(`reportCompare.${side}`)}</label>
            <ReportAttachment key={`${side}:${reset}`} label={t(`reportCompare.${side}`)} hasDraft={!!draft.text.trim()}
              onUse={(text) => edit(side, { text, review: "pending" })} />
            <textarea id={`report-${side}`} className="field min-h-36 w-full" dir="auto" rows={7} spellCheck={false}
              autoComplete="off" autoCapitalize="off" autoCorrect="off"
              placeholder={t("reportCompare.columns")}
              aria-invalid={!!error?.error} aria-describedby={error?.error ? `report-format report-${side}-error` : "report-format"}
              value={draft.text} onChange={(event) => edit(side, {
                text: event.target.value, review: draft.review === "manual" ? "manual" : "pending",
              })} />
            {draft.review !== "manual" && <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={draft.review === "verified"}
                onChange={(event) => edit(side, { ...draft, review: event.target.checked ? "verified" : "pending" })} />
              {t("reportCompare.verify")}
            </label>}
            {error?.error && <p id={`report-${side}-error`} role="alert" className="text-sm text-unsure-fg">
              {t(`reportCompare.error.${error.error}`).replace("{line}", String(error.line ?? ""))}
            </p>}
          </div>;
        })}
      </div>
      <details className="rounded-lg border border-line p-3">
        <summary className="cursor-pointer text-sm font-semibold">{t("reportCompare.formatHelp")}</summary>
        <p id="report-format" className="mt-2 text-sm">{t("reportCompare.format")}</p>
      </details>
      <div className="flex flex-wrap gap-2">
        <button type="submit" className="btn" disabled={requiresReview}>{t("reportCompare.compare")}</button>
        <button type="button" className="btn-quiet" onClick={() => { setDrafts(EMPTY_REPORTS); setParsed(undefined); setReset(reset + 1); }}>
          {t("reportCompare.clear")}
        </button>
      </div>
    </form>

    {comparison && <ComparisonView rows={comparison} />}
  </main>;
}
