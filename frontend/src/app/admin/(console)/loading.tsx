export default function AdminLoading() {
  return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-56" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-24 w-full" />
        ))}
      </div>
      <div className="skeleton h-64 w-full" />
    </div>
  );
}
