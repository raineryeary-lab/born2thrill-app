import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Born2Thrill — Your house, thoughtfully planned",
  description: "Create a structured brief and practical concept ideas for your German family home.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
