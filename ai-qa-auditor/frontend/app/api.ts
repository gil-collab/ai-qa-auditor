export type AuditInput = {
  ticket_id: string;
  agent?: string;
  channel?: string;
  conversation: string;
  macros_used?: string[];
  tags?: string[];
  customer_csatscore?: number;
};

export type SubScore = {
  score: number;
  evidence: string[];
};

export type SectionResult = {
  score: number;
  subscores: Record<string, SubScore>;
};

export type Sections = {
  effectiveness: SectionResult;
  efficiency: SectionResult;
  tone_and_phrasing: SectionResult;
};

export type ZeroTolerance = {
  triggered: boolean;
  reason?: string | null;
  evidence: string[];
};

export type Metadata = {
  ticket_id: string;
  agent?: string | null;
  channel?: string | null;
  tags?: string[] | null;
  macros_used?: string[] | null;
  model: string;
  rubric_version: string;
  redacted: boolean;
};

export type AuditOutput = {
  sections: Sections;
  zero_tolerance: ZeroTolerance;
  overall: number;
  metadata: Metadata;
};

export async function runAudit(input: AuditInput): Promise<AuditOutput> {
  const base = process.env.NEXT_PUBLIC_AUDIT_API || "http://localhost:8080";
  const res = await fetch(`${base}/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Audit failed: ${res.status} ${res.statusText} - ${text}`);
  }
  return res.json();
}

