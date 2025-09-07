"use client";

import React from "react";
import type { AuditOutput, Sections, SectionResult } from "../app/api";

type Props = {
  data: AuditOutput | null;
};

function Section({ title, section }: { title: string; section: SectionResult }) {
  const entries = Object.entries(section.subscores);
  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">Score: {section.score}</span>
      </div>
      <div className="divide-y">
        {entries.map(([name, sub]) => (
          <div key={name} className="px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium capitalize text-gray-800">{name.replaceAll("_", " ")}</div>
              <div className="text-sm font-semibold text-gray-900">{sub.score}</div>
            </div>
            {sub.evidence?.length ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                {sub.evidence.map((e, idx) => (
                  <li key={idx} className="truncate">“{e}”</li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ScoreCard({ data }: Props) {
  if (!data) return null;
  const s: Sections = data.sections;
  const z = data.zero_tolerance;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Audit Results</h2>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700">
            Overall: {data.overall}
          </span>
          <span
            className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${
              z.triggered ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"
            }`}
          >
            ZTP: {z.triggered ? "Triggered" : "Clear"}
          </span>
        </div>
      </div>

      {z.triggered && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <div className="font-semibold">Zero Tolerance Triggered: {z.reason || "policy breach"}</div>
          {z.evidence?.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {z.evidence.map((ev, i) => (
                <li key={i}>“{ev}”</li>
              ))}
            </ul>
          ) : null}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        <Section title="Effectiveness" section={s.effectiveness} />
        <Section title="Efficiency" section={s.efficiency} />
        <Section title="Tone & Phrasing" section={s.tone_and_phrasing} />
      </div>
    </div>
  );
}

