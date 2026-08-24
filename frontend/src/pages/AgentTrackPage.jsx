import { useState } from "react";
import { LayoutDashboard, MapPin, User, Search } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatusBadge } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import Button from "../components/ui/Button";
import { ErrorState, LoadingState } from "../components/ui/States";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/agent", label: "Dashboard", icon: LayoutDashboard },
  { to: "/agent/track", label: "Track", icon: MapPin },
  { to: "/agent/profile", label: "Profile", icon: User },
];

export default function AgentTrackPage() {
  const [trackingId, setTrackingId] = useState("");
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleTrack(e) {
    e.preventDefault();
    if (!trackingId.trim()) return;
    setLoading(true);
    setError("");
    setOrder(null);
    try {
      const res = await api.get(`/orders/track/${trackingId.trim().toUpperCase()}`);
      setOrder(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Agent">
      <div className="p-6 md:p-8 max-w-2xl mx-auto">
        <h1 className="text-xl font-bold text-ink">Track Shipment</h1>
        <form onSubmit={handleTrack} className="mt-5 flex gap-2">
          <Input placeholder="LM-XXXXXXX" value={trackingId} onChange={(e) => setTrackingId(e.target.value)} className="font-mono uppercase" />
          <Button type="submit" loading={loading}><Search size={16} /> Track</Button>
        </form>
        {error && <div className="mt-6"><ErrorState message={error} /></div>}
        {loading && <div className="mt-6"><LoadingState label="Looking up shipment" /></div>}
        {order && (
          <Card className="mt-6 p-6">
            <div className="flex items-center justify-between">
              <span className="font-mono text-lg font-bold text-ink">{order.tracking_id}</span>
              <StatusBadge status={order.current_status} />
            </div>
            <div className="mt-2 text-sm text-ink-muted">{order.pickup_zone_name} → {order.drop_zone_name}</div>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
