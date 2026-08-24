import { useEffect, useState } from "react";
import { LayoutDashboard, Package, MapPin, User, Loader2 } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatusBadge, Badge } from "../components/ui/Card";
import { LoadingState, EmptyState, ErrorState } from "../components/ui/States";
import Button from "../components/ui/Button";
import { Textarea } from "../components/ui/Input";
import { useToast } from "../context/ToastContext";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/agent", label: "Dashboard", icon: LayoutDashboard },
  { to: "/agent/track", label: "Track", icon: MapPin },
  { to: "/agent/profile", label: "Profile", icon: User },
];

const NEXT_STATUS = {
  ASSIGNED: { label: "Mark picked up", status: "PICKED_UP" },
  PICKED_UP: { label: "Mark in transit", status: "IN_TRANSIT" },
  IN_TRANSIT: { label: "Mark out for delivery", status: "OUT_FOR_DELIVERY" },
  OUT_FOR_DELIVERY: { label: "Mark delivered", status: "DELIVERED" },
};

export default function AgentDashboardPage() {
  const [profile, setProfile] = useState(null);
  const [deliveries, setDeliveries] = useState(null);
  const [error, setError] = useState("");
  const [togglingAvailability, setTogglingAvailability] = useState(false);
  const toast = useToast();

  function load() {
    setError("");
    Promise.all([api.get("/agents/me"), api.get("/agents/me/deliveries")])
      .then(([profileRes, deliveriesRes]) => {
        setProfile(profileRes.data);
        setDeliveries(deliveriesRes.data);
      })
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function toggleAvailability() {
    setTogglingAvailability(true);
    try {
      const res = await api.patch("/agents/me/availability", { is_available: !profile.is_available });
      setProfile(res.data);
      toast.success(res.data.is_available ? "You're now available for new deliveries." : "You're now marked unavailable.");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setTogglingAvailability(false);
    }
  }

  const active = deliveries?.filter((d) => !["DELIVERED", "FAILED"].includes(d.current_status)) || [];
  const closed = deliveries?.filter((d) => ["DELIVERED", "FAILED"].includes(d.current_status)) || [];

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Agent">
      <div className="p-6 md:p-8 max-w-4xl mx-auto">
        {error && <ErrorState message={error} onRetry={load} />}
        {!deliveries && !error && <LoadingState label="Loading your deliveries" />}

        {profile && (
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-ink">My Deliveries</h1>
              <p className="text-sm text-ink-muted mt-0.5">
                Active {active.length} · Closed {closed.length} · Zone {profile.current_zone_name}
              </p>
            </div>
            <button
              onClick={toggleAvailability}
              disabled={togglingAvailability}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-colors
                ${profile.is_available ? "bg-success-bg text-success border-success/20" : "bg-slate-100 text-ink-muted border-border"}`}
            >
              {togglingAvailability && <Loader2 size={14} className="animate-spin" />}
              <span className={`w-2 h-2 rounded-full ${profile.is_available ? "bg-success" : "bg-slate-400"}`} />
              {profile.is_available ? "Available" : "Unavailable"}
            </button>
          </div>
        )}

        {deliveries && deliveries.length === 0 && (
          <Card><EmptyState icon={Package} title="No deliveries assigned" description="New assignments will show up here as soon as an admin assigns them to you." /></Card>
        )}

        {active.length > 0 && (
          <div className="grid sm:grid-cols-2 gap-4 mb-8">
            {active.map((order) => (
              <DeliveryCard key={order.id} order={order} onUpdated={load} />
            ))}
          </div>
        )}

        {closed.length > 0 && (
          <>
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-3">Closed</p>
            <div className="grid sm:grid-cols-2 gap-4">
              {closed.map((order) => (
                <DeliveryCard key={order.id} order={order} readOnly onUpdated={load} />
              ))}
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

function DeliveryCard({ order, readOnly, onUpdated }) {
  const [showFailForm, setShowFailForm] = useState(false);
  const [failureReason, setFailureReason] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const nextStep = NEXT_STATUS[order.current_status];

  async function updateStatus(status, extra = {}) {
    setLoading(true);
    try {
      await api.patch(`/orders/${order.id}/status`, { status, ...extra });
      toast.success(`${order.tracking_id} marked ${status.replace(/_/g, " ").toLowerCase()}.`);
      onUpdated();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitFailure() {
    if (!failureReason.trim()) return;
    await updateStatus("FAILED", { failure_reason: failureReason });
    setShowFailForm(false);
    setFailureReason("");
  }

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <span className="font-mono text-sm font-semibold text-ink">{order.tracking_id}</span>
        <StatusBadge status={order.current_status} />
      </div>
      <p className="text-xs text-ink-muted mt-2">{order.pickup_zone_name} → {order.drop_zone_name} · {order.chargeable_weight} kg · {order.order_type}</p>
      <p className="text-xs text-ink-faint mt-1">{order.drop_address}</p>
      {order.payment_type === "COD" && (
        <div className="mt-2"><Badge tone="warning">Collect COD: ₹{order.total_charge.toFixed(2)}</Badge></div>
      )}

      {!readOnly && !showFailForm && (
        <div className="mt-4 flex gap-2">
          {nextStep && (
            <Button size="sm" loading={loading} onClick={() => updateStatus(nextStep.status)}>
              {nextStep.label}
            </Button>
          )}
          {order.current_status === "OUT_FOR_DELIVERY" && (
            <Button size="sm" variant="danger" onClick={() => setShowFailForm(true)}>
              Mark failed
            </Button>
          )}
        </div>
      )}

      {showFailForm && (
        <div className="mt-4 space-y-2">
          <Textarea rows={2} placeholder="Failure reason (required)" value={failureReason} onChange={(e) => setFailureReason(e.target.value)} />
          <div className="flex gap-2">
            <Button size="sm" variant="danger" loading={loading} onClick={submitFailure}>Confirm failed</Button>
            <Button size="sm" variant="ghost" onClick={() => setShowFailForm(false)}>Cancel</Button>
          </div>
        </div>
      )}
    </Card>
  );
}
