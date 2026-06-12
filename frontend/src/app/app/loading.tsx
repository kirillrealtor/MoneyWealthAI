export default function AppLoading() {
  return (
    <div className="space-y-6">
      <div className="skeleton h-9 w-48" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-28 w-full" />
        ))}
      </div>
      <div className="skeleton h-48 w-full" />
    </div>
  );
}
