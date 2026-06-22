import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Born2Thrill — Ihr Haus, durchdacht geplant",
  description: "Erstellen Sie ein strukturiertes Raumprogramm und praktische Konzeptideen für Ihr Einfamilienhaus.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
