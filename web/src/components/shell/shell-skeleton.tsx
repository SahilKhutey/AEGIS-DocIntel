import { Skeleton } from "@/components/ui/skeleton";

export function ShellSkeleton() {
  return (
    <div
      className="min-h-screen bg-[var(--background)] flex"
      aria-busy="true"
      aria-label="Loading workspace"
    >
      <aside className="hidden lg:block w-64 border-r border-[var(--border)] bg-[var(--surface)] p-4 space-y-4">
        <Skeleton variant="text" className="h-8 w-3/4 mb-6" />
        <Skeleton variant="text" className="h-4 w-1/2 mb-2" />
        <Skeleton variant="text" className="h-9 w-full" />
        <Skeleton variant="text" className="h-9 w-full" />
        <Skeleton variant="text" className="h-9 w-full" />
      </aside>
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-[var(--border)] bg-[var(--surface)] px-6 flex items-center justify-between">
          <Skeleton variant="text" className="h-9 w-40" />
          <Skeleton variant="text" className="h-9 w-64 hidden md:block" />
          <div className="flex gap-2">
            <Skeleton variant="circular" className="h-8 w-8" />
            <Skeleton variant="circular" className="h-8 w-8" />
          </div>
        </header>
        <div className="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
          <Skeleton variant="text" className="h-5 w-48 mb-4" />
          <Skeleton variant="card" className="h-32 w-full" />
          <Skeleton variant="table" className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}
