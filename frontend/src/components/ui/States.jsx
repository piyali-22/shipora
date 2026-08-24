import { AlertCircle, Loader2, PackageOpen } from "lucide-react";
import Button from "./Button";

export const EmptyState = ({ icon: Icon = PackageOpen, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
    <div className="w-12 h-12 rounded-full bg-canvas border border-border flex items-center justify-center mb-4">
      <Icon size={20} className="text-ink-faint" />
    </div>
    <h3 className="text-sm font-semibold text-ink">{title}</h3>
    {description && <p className="mt-1 text-sm text-ink-muted max-w-sm">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

export const LoadingState = ({ label = "Loading" }) => (
  <div className="flex flex-col items-center justify-center py-16 text-ink-muted">
    <Loader2 size={20} className="animate-spin mb-2" />
    <span className="text-sm">{label}…</span>
  </div>
);

export const ErrorState = ({ message = "Something went wrong.", onRetry }) => (
  <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
    <div className="w-12 h-12 rounded-full bg-danger-bg flex items-center justify-center mb-4">
      <AlertCircle size={20} className="text-danger" />
    </div>
    <p className="text-sm text-ink max-w-sm">{message}</p>
    {onRetry && (
      <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
        Try again
      </Button>
    )}
  </div>
);

export const SkeletonLine = ({ className = "" }) => (
  <div className={`animate-pulse bg-slate-100 rounded ${className}`} />
);

export const SkeletonCard = () => (
  <div className="bg-white rounded-2xl border border-border p-5">
    <SkeletonLine className="h-3 w-24 mb-3" />
    <SkeletonLine className="h-7 w-16" />
  </div>
);
