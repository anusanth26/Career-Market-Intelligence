/** Re-mounts on every navigation, so each page eases in once. */
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="pagein">{children}</div>;
}
