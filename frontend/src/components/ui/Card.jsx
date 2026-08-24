export const Card = ({ className = "", children, ...props }) => (
  <div className={`bg-white rounded-2xl border border-border shadow-card ${className}`} {...props}>
    {children}
  </div>
);

export const CardHeader = ({ title, subtitle, action, className = "" }) => (
  <div className={`flex items-start justify-between px-6 py-5 border-b border-border ${className}`}>
    <div>
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {subtitle && <p className="text-xs text-ink-muted mt-0.5">{subtitle}</p>}
    </div>
    {action}
  </div>
);

export const StatCard = ({ label, value, sublabel, icon: Icon, accent = "ink" }) => {
  const accentClass = {
    ink: "text-ink",
    brand: "text-brand-600",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  }[accent];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</span>
        {Icon && <Icon size={16} className="text-ink-faint" />}
      </div>
      <div className={`mt-2 text-2xl font-bold font-mono tabular-nums ${accentClass}`}>{value}</div>
      {sublabel && <p className="mt-1 text-xs text-ink-muted">{sublabel}</p>}
    </Card>
  );
};

const STATUS_STYLES = {
  CREATED: "bg-slate-100 text-slate-700",
  ASSIGNED: "bg-brand-50 text-brand-700",
  PICKED_UP: "bg-brand-50 text-brand-700",
  IN_TRANSIT: "bg-brand-50 text-brand-700",
  OUT_FOR_DELIVERY: "bg-warning-bg text-warning",
  DELIVERED: "bg-success-bg text-success",
  FAILED: "bg-danger-bg text-danger",
  RESCHEDULED: "bg-warning-bg text-warning",
};

export const StatusBadge = ({ status }) => (
  <span
    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide
      ${STATUS_STYLES[status] || "bg-slate-100 text-slate-700"}`}
  >
    {status?.replace(/_/g, " ")}
  </span>
);

export const Badge = ({ children, tone = "default" }) => {
  const toneClass = {
    default: "bg-slate-100 text-slate-700",
    brand: "bg-brand-50 text-brand-700",
    success: "bg-success-bg text-success",
    warning: "bg-warning-bg text-warning",
    danger: "bg-danger-bg text-danger",
  }[tone];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${toneClass}`}>
      {children}
    </span>
  );
};
