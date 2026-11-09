import type { Metadata } from "next";
import { Archivo, Literata } from "next/font/google";
import FilterBar from "@/components/FilterBar";
import TopBar from "@/components/TopBar";
import { FilterProvider } from "@/lib/filters";
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
        <FilterProvider>
          <TopBar />
          <FilterBar />
          <main className="dash">{children}</main>
        </FilterProvider>
      </body>
    </html>
  );
}
