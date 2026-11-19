"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { Notice, PageHeader, StatusChip } from "@/components/ui";
import { ReadAloud } from "@/components/Voice";
import { api, FHIR_SANDBOX } from "@/lib/api";
import { conditionLabel, rowLabel } from "@/lib/fixtures";
import { useI18n } from "@/lib/i18n";
import { real } from "@/lib/real";
import { useSession } from "@/lib/session";

export default function MyResult() {
  const { t, lang, level } = useI18n();
  const { persona } = useSession();
  const qc = useQueryClient();
  const results = useQuery({ queryKey: ["results"], queryFn: api.results });
  const expl = useQuery({ queryKey: ["expl", lang, level], queryFn: () => api.explanation(lang, level) });
  const talk = useMutation({ mutationFn: () => api.requestCounselling(), onSuccess: () => qc.invalidateQueries({ queryKey: ["referral"] }) });
  return (
    <section className="space-y-6">
      <PageHeader title={t("result.title")} lead={t("result.lead")}
        action={<Link className="btn-quiet" href="/report-compare">{t("reportCompare.title")}</Link>} />
      {FHIR_SANDBOX && (persona === "person_a" || persona === "person_b") && <FhirReportPreview key={persona} />}
      <div className="card-flush" data-demo="results">
        {results.isLoading && <p className="p-5 text-muted">{t("loading")}</p>}
        <ul className="px-5">
          {results.data?.map((r) => (
            <li key={r.condition_id} className="row">
              <span className="font-medium">{rowLabel(r, lang)}</span>
              <StatusChip status={r.status} />
            </li>
          ))}
        </ul>
      </div>
      <Notice>{t("result.carrierNote")}</Notice>
      <div className="card" data-demo="explanation">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{t("result.explanation")}</h2>
          <ReadAloud text={expl.data?.blocks.join(" ") ?? ""} />
        </div>
        <div className="max-w-read space-y-3" data-testid="explanation">
          {expl.data?.blocks.map((b, i) => <p key={i}>{b}</p>)}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn" data-demo="talk" disabled={talk.isSuccess} onClick={() => talk.mutate()}>
          {talk.isSuccess ? <CheckCircle2 aria-hidden className="h-4 w-4" /> : <MessageSquareText aria-hidden className="h-4 w-4" />}
          {talk.isSuccess ? t("result.talkDone") : t("result.talk")}
        </button>
      </div>
    </section>
  );
}

function FhirReportPreview() {
  const { t, lang } = useI18n();
  const preview = useMutation({ mutationFn: real.previewFhirReport });
  const report = preview.data;
  return <section className="card space-y-3" aria-labelledby="fhir-preview-heading">
    <h2 id="fhir-preview-heading" className="text-lg font-semibold">{t("fhirPreview.title")}</h2>
    <p>{t("fhirPreview.description")}</p>
    <button className="btn-quiet" disabled={preview.isPending} onClick={() => preview.mutate()}>
      {t(preview.isPending ? "loading" : "fhirPreview.load")}
    </button>
    {preview.isError && <p role="alert">{t("fhirPreview.error")}</p>}
    {report && <div className="space-y-2">
      <p role="status">{t(`fhirPreview.${report.state}`)}</p>
      {report.issued_at && <p>{t("labSandbox.revision")} {report.version} · <time dateTime={report.issued_at}>
        {new Date(report.issued_at).toLocaleString(lang)}
      </time></p>}
      {!!report.findings.length && <ul>{report.findings.map((finding) => <li className="row" key={finding.source_id}>
        <div>
          <span>{conditionLabel(finding.condition_id, lang)}</span>
          <small className="block text-muted break-all">{finding.source_id}</small>
        </div>
        <StatusChip status={finding.status} />
      </li>)}</ul>}
    </div>}
  </section>;
}
