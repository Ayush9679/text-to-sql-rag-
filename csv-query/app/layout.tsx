import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "csv-query — Instant AI Text-to-SQL for CSVs",
  description: "Upload any CSV and ask natural language questions with instant SQL generation, tables, and charts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#090D16] text-slate-100 selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
