import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LayoutDashboard, Package, MapPin, Bell, User, Plus } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { StatCard, Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Card";
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

export default function CustomerDashboardPage() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/orders")
      .then((res) => setOrders(res.data))
      .catch((err) => setError(err.message));
  }, []);

  const counts = orders
    ? {
        active: orders.filter((o) => !["DELIVERED", "FAILED"].includes(o.current_status)).length,
        inTransit: orders.filter((o) => ["PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"].includes(o.current_status)).length,
        delivered: orders.filter((o) => o.current_status === "DELIVERED").length,
        failed: orders.filter((o) => o.current_status === "FAILED").length,
      }
    : null;

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Customer">
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-ink">Dashboard</h1>
            <p className="text-sm text-ink-muted mt-0.5">A quick view of everything you're shipping.</p>
          </div>
          <Link to="/dashboard/new-shipment">
            <Button>
              <Plus size={16} /> New Shipment
            </Button>
          </Link>
        </div>

        {error && <ErrorState message={error} />}

        {!error && counts && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Active Shipments" value={counts.active} accent="brand" />
            <StatCard label="In Transit" value={counts.inTransit} accent="brand" />
            <StatCard label="Delivered" value={counts.delivered} accent="success" />
            <StatCard label="Failed" value={counts.failed} accent="danger" />
          </div>
        )}

        <Card>
          <div className="px-6 py-5 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink">Recent Orders</h3>
            <Link to="/dashboard/orders" className="text-xs font-medium text-brand-600 hover:text-brand-700">
              View all
            </Link>
          </div>

          {!orders && !error && <LoadingState label="Loading orders" />}

          {orders && orders.length === 0 && (
            <EmptyState
              icon={Package}
              title="No shipments yet"
              description="Once you create a shipment, it'll show up here with live status."
              action={
                <Link to="/dashboard/new-shipment">
                  <Button size="sm">Create your first shipment</Button>
                </Link>
              }
            />
          )}

          {orders && orders.length > 0 && (
            <div className="divide-y divide-border">
              {orders.slice(0, 5).map((o) => (
                <Link
                  key={o.id}
                  to={`/dashboard/orders/${o.id}`}
                  className="flex items-center justify-between px-6 py-4 hover:bg-canvas transition-colors"
                >
                  <div>
                    <p className="text-sm font-mono font-semibold text-ink">{o.tracking_id}</p>
                    <p className="text-xs text-ink-muted mt-0.5">
                      {o.pickup_zone_name} → {o.drop_zone_name}
                    </p>
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
