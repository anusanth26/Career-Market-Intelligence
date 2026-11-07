import type { Metadata } from "next";
import { Archivo, Literata } from "next/font/google";
import Rail from "@/components/Rail";
import "./globals.css";

const ui = Archivo({ subsets: ["latin"], variable: "--font-ui", axes: ["wdth"], display: "swap" });
const read = Literata({ subsets: ["latin"], variable: "--font-read", display: "swap" });

export const metadata: Metadata = {
  title: { default: "Career Market Intelligence", template: "%s | Career Market Intelligence" },
  description: "What 14,085 Indian job postings say about pay and skills, with a salary model that returns a range.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={`${ui.variable} ${read.variable}`}>
      <body>
        <div className="shell">
          <Rail />
          <main className="page">{children}</main>
        </div>
      </body>
    </html>
  );
}
