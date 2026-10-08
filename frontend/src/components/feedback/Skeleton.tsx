import { cn } from "@/utils/cn";

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("app-skeleton", className)} />;
}

/** Placeholder shaped like a generated dashboard, shown while a workspace loads. */
export function CanvasSkeleton({ label }: { label: string }) {
  return (
    <div role="status" aria-label={label} className="mx-auto w-full max-w-5xl p-8">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="mt-2 h-4 w-40" />
      <div className="mt-6 grid grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-24" />
        ))}
      </div>
      <div className="mt-4 grid grid-cols-12 gap-4">
        <Skeleton className="col-span-7 h-64" />
        <Skeleton className="col-span-5 h-64" />
      </div>
      <Skeleton className="mt-4 h-48" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
