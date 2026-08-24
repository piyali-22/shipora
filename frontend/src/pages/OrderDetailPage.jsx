import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, MapPin, Bell, User, Plus, Calendar } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatusBadge } from "../components/ui/Card";
import { LoadingState, ErrorState } from "../components/ui/States";
import Button from "../components/ui/Button";
import { Input, Label } from "../components/ui/Input";
import { useToast } from "../context/ToastContext";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dashboard/new-shipment", label: "New Shipment", icon: Plus },
  { to: "/dashboard/orders", label: "My Orders", icon: Package },
  { to: "/dashboard/track", label: "Track", icon: MapPin },
  { to: "/dashboard/notifications", label: "Notifications", icon: Bell },
  { to: "/dashboard/profile", label: "Profile", icon: User },
];

export default function OrderDetailPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [rescheduleDate, setRescheduleDate] = useState("");
  const [rescheduling, setRescheduling] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  function load() {
    setError("");
    api.get(`/orders/${orderId}`).then((res) => setOrder(res.data)).catch((err) => setError(err.message));
  }

  useEffect(load, [orderId]);

  async function handleReschedule(e) {
    e.preventDefault();
    setRescheduling(true);
    try {
      await api.post(`/orders/${orderId}/reschedule`, { rescheduled_date: new Date(rescheduleDate).toISOString() });
      toast.success("Delivery rescheduled.");
      load();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRescheduling(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Customer">
      <div className="p-6 md:p-8 max-w-3xl mx-auto">
        {error && <ErrorState message={error} onRetry={load} />}
        {!order && !error && <LoadingState label="Loading shipment" />}

        {order && (
          <>
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Tracking ID</p>
                <h1 className="text-2xl font-bold font-mono text-ink mt-0.5">{order.tracking_id}</h1>
              </div>
              <StatusBadge status={order.current_status} />
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <Card className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">Route</p>
                <p className="text-sm text-ink">{order.pickup_zone_name} → {order.drop_zone_name}</p>
                <div className="mt-3 text-xs text-ink-muted space-y-1">
                  <p><span className="text-ink-faint">Pickup:</span> {order.pickup_address}</p>
                  <p><span className="text-ink-faint">Drop:</span> {order.drop_address}</p>
                </div>
              </Card>
              <Card className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">Charges</p>
                <div className="space-y-1.5 font-mono text-xs">
                  <Row label="Billed weight" value={`${order.chargeable_weight} kg`} />
                  <Row label="Base charge" value={`₹${order.base_charge.toFixed(2)}`} />
                  <Row label="Weight charge" value={`₹${order.weight_charge.toFixed(2)}`} />
                  {order.cod_surcharge > 0 && <Row label="COD surcharge" value={`₹${order.cod_surcharge.toFixed(2)}`} />}
                  <div className="h-px bg-border my-2" />
                  <Row label="Total" value={`₹${order.total_charge.toFixed(2)}`} bold />
                </div>
              </Card>
            </div>

            {order.current_status === "FAILED" && (
              <Card className="p-5 mb-6 border-warning/30">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar size={16} className="text-warning" />
                  <h3 className="text-sm font-semibold text-ink">Reschedule delivery</h3>
                </div>
                <form onSubmit={handleReschedule} className="flex items-end gap-3">
                  <div className="flex-1">
                    <Label>New delivery date</Label>
                    <Input type="datetime-local" required value={rescheduleDate} onChange={(e) => setRescheduleDate(e.target.value)} />
                  </div>
                  <Button type="submit" loading={rescheduling}>Reschedule</Button>
                </form>
              </Card>
            )}

            <Card>
              <div className="px-6 py-4 border-b border-border">
                <h3 className="text-sm font-semibold text-ink">Tracking Timeline</h3>
              </div>
              <div className="px-6 py-5">
                {[...order.tracking_history].reverse().map((event, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center pt-1">
                      <div className={`w-2 h-2 rounded-full ${i === 0 ? "bg-brand-600" : "bg-slate-300"}`} />
                      {i < order.tracking_history.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
                    </div>
                    <div className="pb-5">
                      <p className="text-sm font-semibold text-ink">{event.status.replace(/_/g, " ")}</p>
                      <p className="text-xs text-ink-muted mt-0.5 font-mono">
                        {new Date(event.timestamp).toLocaleString()} — {event.actor_name} ({event.actor_role})
                      </p>
                      {event.note && <p className="text-xs text-ink-faint mt-1">{event.note}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

function Row({ label, value, bold }) {
  return (
    <div className="flex justify-between">
      <span className="text-ink-faint">{label}</span>
      <span className={bold ? "font-bold text-ink" : "text-ink-muted"}>{value}</span>
    </div>
  );
}
