export function AuthShell({
  title,
  subtitle,
  footer,
  children,
}: {
  title: string;
  subtitle: string;
  footer: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-md flex-1 px-4 py-12 sm:py-16">
      <h1 className="font-serif text-4xl tracking-tight text-ink">{title}</h1>
      <p className="mt-2 text-muted-ink">{subtitle}</p>
      <div className="mt-8">{children}</div>
      <p className="mt-8 border-t border-line pt-6 text-sm text-muted-ink">{footer}</p>
    </main>
  );
}

export function FormSkeleton({ fields }: { fields: number }) {
  return (
    <div className="space-y-5" aria-busy>
      {Array.from({ length: fields }, (_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-20 animate-pulse rounded bg-surface" />
          <div className="h-11 animate-pulse rounded-lg bg-surface" />
        </div>
      ))}
      <div className="h-11 animate-pulse rounded-full bg-surface" />
    </div>
  );
}
