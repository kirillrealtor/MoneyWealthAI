export function LegalShell({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto max-w-3xl px-5 pt-36 pb-24">
      <h1 className="text-4xl font-medium tracking-tight">{title}</h1>
      <p className="mt-2 text-sm text-fg-subtle">Last updated {updated}</p>
      <div className="mt-4 rounded-[12px] border border-warning/25 bg-warning/5 px-4 py-3 text-sm text-fg-muted">
        Template for review — replace with counsel-approved language before launch.
      </div>
      <div className="mt-8 space-y-5 text-sm leading-relaxed text-fg-muted [&_h2]:mt-8 [&_h2]:text-lg [&_h2]:font-medium [&_h2]:text-fg [&_a]:text-brand [&_a]:underline">
        {children}
      </div>
    </main>
  );
}
