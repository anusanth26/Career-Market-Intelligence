"use client";
import { useEffect, useState } from "react";

/** A short "on this page" list built from the page's h2 headings. */
export default function PageNav() {
  const [items, setItems] = useState<{ id: string; text: string }[]>([]);
  useEffect(() => {
    const hs = Array.from(document.querySelectorAll("main h2")) as HTMLElement[];
    setItems(hs.map((h, i) => {
      if (!h.id) h.id = `s${i}-${(h.textContent || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40)}`;
      return { id: h.id, text: h.textContent || "" };
    }));
  }, []);
  if (items.length < 2) return null;
  return (
    <nav className="jump" aria-label="On this page">
      <span>On this page</span>
      {items.map((i) => <a key={i.id} href={`#${i.id}`}>{i.text.replace(/\?$/, "")}</a>)}
    </nav>
  );
}
