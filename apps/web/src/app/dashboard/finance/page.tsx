"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { gbp } from "@/lib/format";
import { withLoadError } from "@/lib/load-errors";

type FreeAgentInfo = {
  state: string;
  message: string;
  can_sync: boolean;
  organisation_name?: string | null;
  last_sync_at?: string | null;
};

type PaymentCandidate = { transaction_id: string; description: string; amount_gbp: string; date: string; status: "unique_candidate" | "ambiguous" | "unmatched"; invoice_number: string | null; invoice_id: string | null; local_confirmation_allowed?: boolean };
type CandidateReport = { transactions: PaymentCandidate[]; basis: string; limit: number };

type ReceiptMatch = { receipt_id: string; transaction_id: string; merchant: string | null; receipt_total: string | null; receipt_date: string | null; bank_description: string; bank_amount: string; bank_date: string; eligible: boolean };

export default function FinancePage() {
  const [receiptMatches, setReceiptMatches] = useState<ReceiptMatch[] | null>(null);
  const [receiptError, setReceiptError] = useState(false);
  const [receiptBusy, setReceiptBusy] = useState(false);
  const [receiptMessage, setReceiptMessage] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<CandidateReport | null>(null);
  const [candidateError, setCandidateError] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);
  const [paymentBusy, setPaymentBusy] = useState(false);
  const [reconciliation, setReconciliation] = useState<Record<string, number | string> | null>(null);
  const [reconciliationError, setReconciliationError] = useState(false);
  const [status, setStatus] = useState<{ freeagent: FreeAgentInfo; mettle_feed: string } | null>(
    null,
  );
  const [territories, setTerritories] = useState<
    Array<{ territory_code: string; estimated_profit_gbp: number }>
  >([]);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    setReceiptError(false);
    setReceiptMatches(null);
    apiGet<ReceiptMatch[]>("/api/v1/finance/bookkeeping/receipts/match-review", token).then(setReceiptMatches).catch(withLoadError(() => setReceiptError(true)));
    setCandidateError(false);
    setCandidates(null);
    apiGet<CandidateReport>("/api/v1/finance/insights/reconciliation/payment-candidates", token)
      .then(setCandidates).catch(withLoadError(() => { setCandidates(null); setCandidateError(true); }));
    setReconciliationError(false);
    apiGet<Record<string, number | string>>("/api/v1/finance/insights/reconciliation", token).then(setReconciliation).catch(withLoadError(() => { setReconciliation(null); setReconciliationError(true); }));
    apiGet<{ freeagent: FreeAgentInfo; mettle_feed: string }>("/api/v1/finance/status", token)
      .then(setStatus)
      .catch(withLoadError(() => setStatus(null)));
    apiGet<Array<{ territory_code: string; estimated_profit_gbp: number }>>(
      "/api/v1/finance/profitability/territories",
      token,
    )
      .then(setTerritories)
      .catch(withLoadError(() => setTerritories([])));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function connectFreeAgent() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setSyncMsg(null);
    try {
      const { authorize_url } = await apiGet<{ authorize_url: string }>(
        "/api/v1/finance/freeagent/authorize",
        token,
      );
      window.location.href = authorize_url;
    } catch {
      setSyncMsg("Could not start FreeAgent connect — check API env credentials.");
    } finally {
      setBusy(false);
    }
  }

  async function syncFreeAgent(full: boolean) {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setSyncMsg(null);
    try {
      const path = full ? "/api/v1/finance/freeagent/sync/full" : "/api/v1/finance/freeagent/sync";
      const result = await apiPost<Record<string, string | number>>(
        path,
        {},
        token,
      );
      setSyncMsg(
        full
          ? JSON.stringify(result).slice(0, 200)
          : String((result as { message?: string }).message ?? "Sync finished"),
      );
      load();
    } catch {
      setSyncMsg("Sync failed — see Finance status message.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmPayment(item: PaymentCandidate) {
    const token = getToken();
    if (!token || !item.invoice_id || !item.local_confirmation_allowed || paymentBusy) return;
    if (!window.confirm("Confirm you have independently verified this payment belongs to invoice " + item.invoice_number + "?")) return;
    setPaymentBusy(true);
    setPaymentMessage(null);
    try {
      await apiPost("/api/v1/finance/transactions/" + item.transaction_id + "/confirm-payment", { invoice_id: item.invoice_id, confirmed: true }, token);
      setPaymentMessage("Local payment recorded. Refreshing records.");
      load();
    } catch {
      setPaymentMessage("Payment could not be confirmed. Refresh and verify the invoice and transaction.");
    } finally {
      setPaymentBusy(false);
    }
  }

  async function confirmReceipt(item: ReceiptMatch) {
    const token = getToken();
    if (!token || !item.eligible || receiptBusy || !window.confirm("Have you checked the original receipt against this bank transaction?")) return;
    setReceiptBusy(true);
    setReceiptMessage(null);
    try {
      await apiPost("/api/v1/finance/bookkeeping/receipts/" + item.receipt_id + "/confirm-match", { transaction_id: item.transaction_id, confirmed: true }, token);
      setReceiptMessage("Receipt match confirmed locally. Nothing posted to FreeAgent.");
      load();
    } catch {
      setReceiptMessage("Could not confirm receipt. Review the original records.");
    } finally { setReceiptBusy(false); }
  }

  const fa = status?.freeagent;

  return (
    <div>
      <header className="rounded-2xl bg-slate-950 p-5 text-white"><p className="text-xs font-semibold uppercase tracking-widest text-amber-300">SurfaceCoat · AI Accountant</p><h1 className="mt-2 text-2xl font-semibold">Finance command centre</h1><p className="mt-2 text-sm text-slate-300">Review, reconcile and understand your business finances.</p></header>
      <p className="mt-2 text-sm text-slate-600">
        SurfaceCoat Ltd — FreeAgent remains the authoritative books. Mettle feeds through FreeAgent when linked.
        Use <strong>Company setup</strong> for incorporation details and statutory checklist.
      </p>

      {fa && (
        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <h2 className="font-semibold text-slate-900">FreeAgent</h2>
          <p className="mt-1 text-slate-600">
            {fa.state} — {fa.message}
            {fa.organisation_name ? ` (${fa.organisation_name})` : null}
          </p>
          {fa.last_sync_at ? (
            <p className="mt-1 text-xs text-slate-500">Last sync: {fa.last_sync_at}</p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {fa.state !== "connected" ? (
              <button
                type="button"
                disabled={busy}
                onClick={connectFreeAgent}
                className="rounded-md bg-emerald-800 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-900 disabled:opacity-50"
              >
                Connect FreeAgent
              </button>
            ) : (
              <>
                <button
                  type="button"
                  disabled={busy || !fa.can_sync}
                  onClick={() => syncFreeAgent(false)}
                  className="rounded-md border border-emerald-800 px-4 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-50 disabled:opacity-50"
                >
                  Sync invoices
                </button>
                <button
                  type="button"
                  disabled={busy || !fa.can_sync}
                  onClick={() => syncFreeAgent(true)}
                  className="rounded-md bg-emerald-800 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-900 disabled:opacity-50"
                >
                  Full sync (invoices + bank)
                </button>
              </>
            )}
          </div>
          {syncMsg ? <p className="mt-2 text-xs text-slate-600">{syncMsg}</p> : null}
        </section>
      )}

      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-2"><h2 className="font-semibold">Reconciliation centre</h2><button type="button" onClick={load} className="rounded-lg border px-3 py-2 text-xs">Refresh</button></div>
        {reconciliationError ? <p role="alert" className="mt-3 text-sm text-red-700">Could not load reconciliation records. Try refreshing.</p> : !reconciliation ? <p className="mt-3 text-sm">Loading records…</p> : <>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {Object.entries({ imported_bank_lines: "Imported bank lines", reconciled_bank_lines: "Marked reconciled", unreconciled_bank_lines: "Awaiting reconciliation", flagged_duplicates: "Flagged duplicates", receipts_without_bank_match: "Unmatched receipts", pending_reviews: "Pending reviews" }).map(([key, label]) => (
              <div key={key} className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-600">{label}</p><p className="mt-2 text-2xl font-semibold tabular-nums">{reconciliation[key] ?? "Unknown"}</p></div>
            ))}
          </div><p className="mt-3 text-xs text-slate-500">{reconciliation.basis}</p>
        </>}
      </section>
      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="font-semibold">Incoming payment review</h2>
        <p className="mt-1 text-xs text-slate-600">Verify suggested matches independently. FreeAgent records must be reconciled in FreeAgent.</p>
        {paymentMessage && <p role="status" className="mt-2 text-sm">{paymentMessage}</p>}
        {candidateError ? <p role="alert" className="mt-3 text-sm text-red-700">Could not load payment suggestions. Use Refresh above to retry.</p> : !candidates ? <p className="mt-3 text-sm">Loading payment suggestions…</p> : <>
          {candidates.transactions.length === 0 ? <p className="mt-3 text-sm text-slate-600">No eligible incoming payments found in imported records.</p> : <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {candidates.transactions.map((item) => <article key={item.transaction_id} className="min-w-0 rounded-lg border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2"><strong>{gbp(Number(item.amount_gbp))}</strong><span className="rounded bg-slate-100 px-2 py-1 text-xs">{item.status === "unique_candidate" ? "Suggested match" : item.status === "ambiguous" ? "Multiple possible invoices" : "Unmatched"}</span></div>
              <p className="mt-2 break-words text-sm">{item.description}</p>
              <p className="text-xs text-slate-600">{item.date}</p>
              {item.invoice_number && <p className="mt-2 text-sm">Possible invoice: {item.invoice_number}</p>}
              {item.local_confirmation_allowed && <button type="button" disabled={paymentBusy} onClick={() => confirmPayment(item)} className="mt-3 rounded-lg bg-emerald-800 px-3 py-2 text-sm text-white disabled:opacity-50">Confirm verified local payment</button>}
            </article>)}
          </div>}
          <p className="mt-3 text-xs text-slate-500">{candidates.basis} Showing up to {candidates.limit} transactions.</p>
        </>}
      </section>
      <section className="mt-6 rounded-xl border bg-white p-4">
        <h2 className="font-semibold">Receipt match review</h2>
        <p className="mt-1 text-xs text-slate-600">Compare original receipts and bank records before confirming. No external posting.</p>
        {receiptMessage && <p role="status" className="mt-2 text-sm">{receiptMessage}</p>}
        {receiptError ? <p role="alert" className="mt-3 text-sm text-red-700">Unable to load receipt matches. Refresh to retry.</p> : !receiptMatches ? <p className="mt-3 text-sm">Loading receipts…</p> : receiptMatches.length === 0 ? <p className="mt-3 text-sm">No suggested receipt matches awaiting review.</p> : <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {receiptMatches.map(item => <article key={item.receipt_id} className="rounded-lg border p-3 text-sm">
            <strong>{item.merchant || "Unknown merchant"}</strong>
            <p>Receipt: {item.receipt_total === null ? "Unknown amount" : gbp(Number(item.receipt_total))} · {item.receipt_date || "Unknown date"}</p>
            <p className="mt-2 break-words">{item.bank_description} · {gbp(Number(item.bank_amount))} · {item.bank_date}</p>
            <button type="button" disabled={receiptBusy || !item.eligible} onClick={() => confirmReceipt(item)} className="mt-3 rounded-lg bg-emerald-800 px-3 py-2 text-white disabled:opacity-50">Confirm receipt match</button>
          </article>)}
        </div>}
      </section>
      <section className="mt-6">
        <h2 className="font-semibold">Territory estimated quoted contribution</h2>
        <ul className="mt-2 text-sm">
          {territories.map((t) => (
            <li key={t.territory_code} className="border-b py-1">
              {t.territory_code} — est. profit {gbp(t.estimated_profit_gbp)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}