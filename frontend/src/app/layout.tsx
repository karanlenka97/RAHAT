import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RAHAT | Rural Assistance & Healthcare Access Tele-network",
  description: "Intelligent Healthcare Access & Emergency Referral Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-full flex flex-col bg-slate-950 text-slate-100 antialiased`}>
        {children}
      </body>
    </html>
  );
}
