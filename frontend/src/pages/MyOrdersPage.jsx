import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LayoutDashboard, Package, MapPin, Bell, User, Plus } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatusBadge } from "../components/ui/Card";
import { LoadingState, EmptyState, ErrorState } from "../components/ui/States";
import Button from "../components/ui/Button";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dashboard/new-shipment", label: "New Shipment", icon: Plus },
  { to: "/dashboard/orders", label: "My Orders", icon: Package },
  { to: "/dashboard/track", label: "Track", icon: MapPin },
  { to: "/dashboard/notifications", label: "Notifications", icon: Bell },
  { to: "/dashboard/profile", label: "Profile", icon: User },
];

export default function MyOrdersPage() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setOrders(null);
    api.get("/orders").then((res) => setOrders(res.data)).catch((err) => setError(err.message));
  }

  useEffect(load, []);

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Customer">
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-ink">My Orders</h1>
            <p className="text-sm text-ink-muted mt-0.5">Shipment history.</p>
          </div>
          <Link to="/dashboard/new-shipment">
            <Button><Plus size={16} /> New Shipment</Button>
          </Link>
        </div>

        <Card>
          {!orders && !error && <LoadingState label="Loading orders" />}
          {error && <ErrorState message={error} onRetry={load} />}
          {orders && orders.length === 0 && (
            <EmptyState
              icon={Package}
              title="No shipments on record"
              action={<Link to="/dashboard/new-shipment"><Button size="sm">Create your first shipment</Button></Link>}
            />
          )}
          {orders && orders.length > 0 && (
            <div className="divide-y divide-border">
              {orders.map((o) => (
                <Link key={o.id} to={`/dashboard/orders/${o.id}`} className="flex items-center justify-between px-6 py-4 hover:bg-canvas transition-colors">
                  <div>
                    <p className="text-sm font-mono font-semibold text-ink">{o.tracking_id}</p>
                    <p className="text-xs text-ink-muted mt-0.5">{o.pickup_zone_name} → {o.drop_zone_name}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-mono text-ink">₹{o.total_charge.toFixed(2)}</span>
                    <StatusBadge status={o.current_status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}
