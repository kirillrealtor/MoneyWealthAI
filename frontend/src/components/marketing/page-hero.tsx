export function PageHero({
  kicker,
  title,
  em,
  rest,
  sub,
}: {
  kicker: string;
  title: string;
  em?: string;
  rest?: string;
  sub: string;
}) {
  return (
    <section className="mx-auto max-w-3xl px-5 pt-36 pb-12 text-center">
      <span className="text-xs font-medium uppercase tracking-[0.2em] text-brand animate-[rise_0.5s_ease-out_both]">
        {kicker}
      </span>
      <h1 className="mt-4 text-balance text-4xl font-medium leading-tight tracking-tight sm:text-6xl animate-[rise_0.5s_ease-out_0.05s_both]">
        {title} {em && <span className="font-display italic text-aurora">{em}</span>} {rest}
      </h1>
      <p className="mx-auto mt-5 max-w-xl text-balance text-lg text-fg-muted animate-[rise_0.5s_ease-out_0.1s_both]">
        {sub}
      </p>
    </section>
  );
}
