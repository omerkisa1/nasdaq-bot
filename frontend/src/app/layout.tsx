import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Otonom Trade Kartı Sistemi",
  description: "Penny hisse momentum trade sinyalleri",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">{children}</body>
    </html>
  );
}
