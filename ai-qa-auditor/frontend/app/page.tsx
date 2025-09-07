"use client";

import React from "react";
import { runAudit, type AuditOutput } from "./api";
import ScoreCard from "../components/ScoreCard";

const channels = [
  { value: "", label: "Select channel (optional)" },
  { value: "email", label: "Email" },
  { value: "chat", label: "Chat" },
  { value: "phone", label: "Phone" }
];

export default function Page() {
  const [ticketId, setTicketId] = React.useState("");
  const [channel, setChannel] = React.useState("");
  const [conversation, setConversation] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AuditOutput | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!ticketId || !conversation) {
      setError("ticket_id and conversation are required");
      return;
    }
    setLoading(true);
    try {
      const data = await runAudit({ ticket_id: ticketId, channel: channel || undefined, conversation });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">AI QA Auditor</h1>
          <p className="mt-1 text-sm text-gray-600">Paste a transcript and run an audit. API: {process.env.NEXT_PUBLIC_AUDIT_API || "http://localhost:8080"}</p>
        </div>
      </header>

      <form onSubmit={onSubmit} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-gray-700">Ticket ID</label>
            <input
              type="text"
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="T-12345"
              value={ticketId}
              onChange={(e) => setTicketId(e.target.value)}
              required
            />
          </div>
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-gray-700">Channel</label>
            <select
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
            >
              {channels.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700">Conversation Transcript</label>
          <textarea
            className="mt-1 h-64 w-full resize-y rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Customer: ...\nAgent: ..."
            value={conversation}
            onChange={(e) => setConversation(e.target.value)}
            required
          />
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            {loading ? "Running..." : "Run Audit"}
          </button>
          {error && <span className="text-sm text-red-600">{error}</span>}
        </div>
      </form>

      <ScoreCard data={result} />
    </main>
  );
}

