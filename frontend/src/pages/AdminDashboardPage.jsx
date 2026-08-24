import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { LayoutDashboard, Package, Users, Map, CreditCard, Bell } from "lucide-react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatCard, StatusBadge } from "../components/ui/Card";
import { LoadingState, ErrorState, EmptyState } from "../components/ui/States";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard },
  { to: "/admin/orders", label: "Orders", icon: Package },
  { to: "/admin/agents", label: "Agents", icon: Users },
  { to: "/admin/zones", label: "Zones", icon: Map },
  { to: "/admin/rates", label: "Rate Cards", icon: CreditCard },
  { to: "/admin/notifications", label: "Notifications", icon: Bell },
];

const STATUS_COLORS = {
  CREATED: "#94A3B8",
  ASSIGNED: "#818CF8",
  PICKED_UP: "#6366F1",
  IN_TRANSIT: "#4F46E5",
  OUT_FOR_DELIVERY: "#D97706",
  DELIVERED: "#059669",
  FAILED: "#DC2626",
  RESCHEDULED: "#D97706",
};

export default function AdminDashboardPage() {
  const [orders, setOrders] = useState(null);
  const [agents, setAgents] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    Promise.all([api.get("/orders"), api.get("/agents")])
      .then(([o, a]) => { setOrders(o.data); setAgents(a.data); })
      .catch((err) => setError(err.message));
  }
  useEffect(load, []);

  const stats = useMemo(() => {
    if (!orders) return null;
    const today = new Date().toDateString();
    return {
      total: orders.length,
      today: orders.filter((o) => new Date(o.created_at).toDateString() === today).length,
      inTransit: orders.filter((o) => ["PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"].includes(o.current_status)).length,
      delivered: orders.filter((o) => o.current_status === "DELIVERED").length,
      failed: orders.filter((o) => o.current_status === "FAILED").length,
      revenue: orders.reduce((sum, o) => sum + o.total_charge, 0),
      activeAgents: agents?.filter((a) => a.is_available && a.is_active).length ?? 0,
    };
  }, [orders, agents]);

  const statusChartData = useMemo(() => {
    if (!orders) return [];
    const counts = {};
    orders.forEach((o) => { counts[o.current_status] = (counts[o.current_status] || 0) + 1; });
    return Object.entries(counts).map(([status, value]) => ({ name: status.replace(/_/g, " "), value, status }));
  }, [orders]);

  const zoneChartData = useMemo(() => {
    if (!orders) return [];
    const counts = {};
    orders.forEach((o) => { counts[o.pickup_zone_name] = (counts[o.pickup_zone_name] || 0) + 1; });
    return Object.entries(counts).map(([zone, count]) => ({ zone, count }));
  }, [orders]);

  const successRate = stats && (stats.delivered + stats.failed) > 0
    ? Math.round((stats.delivered / (stats.delivered + stats.failed)) * 100)
    : null;

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Admin">
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <h1 className="text-xl font-bold text-ink mb-1">Dispatch Overview</h1>
        <p className="text-sm text-ink-muted mb-6">Operations at a glance.</p>

        {error && <ErrorState message={error} onRetry={load} />}
        {!orders && !error && <LoadingState label="Loading dashboard" />}

        {stats && (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <StatCard label="Total Orders" value={stats.total} />
              <StatCard label="Orders Today" value={stats.today} accent="brand" />
              <StatCard label="In Transit" value={stats.inTransit} accent="brand" />
              <StatCard label="Delivered" value={stats.delivered} accent="success" />
              <StatCard label="Failed" value={stats.failed} accent="danger" />
              <StatCard label="Active Agents" value={stats.activeAgents} />
              <StatCard label="Revenue" value={`₹${stats.revenue.toFixed(0)}`} accent="brand" />
              <StatCard label="Success Rate" value={successRate !== null ? `${successRate}%` : "—"} accent="success" />
            </div>

            {orders.length > 0 && (
              <div className="grid lg:grid-cols-2 gap-4 mb-6">
                <Card className="p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-4">Orders by Status</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={statusChartData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                        {statusChartData.map((entry) => (
                          <Cell key={entry.status} fill={STATUS_COLORS[entry.status] || "#94A3B8"} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
                <Card className="p-5">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-4">Orders by Pickup Zone</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={zoneChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                      <XAxis dataKey="zone" tick={{ fontSize: 11 }} stroke="#94A3B8" />
                      <YAxis tick={{ fontSize: 11 }} stroke="#94A3B8" allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </div>
            )}

            <Card>
              <div className="px-6 py-4 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-ink">Latest Orders</h3>
                <Link to="/admin/orders" className="text-xs font-medium text-brand-600 hover:text-brand-700">View all</Link>
              </div>
              {orders.length === 0 ? (
                <EmptyState icon={Package} title="No orders yet" />
              ) : (
                <div className="divide-y divide-border">
                  {orders.slice(0, 6).map((o) => (
                    <div key={o.id} className="flex items-center justify-between px-6 py-3.5">
                      <div>
                        <p className="text-sm font-mono font-semibold text-ink">{o.tracking_id}</p>
                        <p className="text-xs text-ink-muted mt-0.5">{o.pickup_zone_name} → {o.drop_zone_name}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-ink">₹{o.total_charge.toFixed(2)}</span>
                        <StatusBadge status={o.current_status} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
