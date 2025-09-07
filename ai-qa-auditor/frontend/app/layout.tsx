import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI QA Auditor",
  description: "Paste a transcript and run a QA audit",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <div className="max-w-5xl mx-auto px-4 py-8">{children}</div>
      </body>
    </html>
  );
}

