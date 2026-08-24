import { useEffect, useMemo, useState } from "react";
import { LayoutDashboard, Package, Users, Map, CreditCard, Bell, Search } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, StatusBadge } from "../components/ui/Card";
import { Input, Select } from "../components/ui/Input";
import { LoadingState, ErrorState, EmptyState } from "../components/ui/States";
import Button from "../components/ui/Button";
import { useToast } from "../context/ToastContext";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard },
  { to: "/admin/orders", label: "Orders", icon: Package },
  { to: "/admin/agents", label: "Agents", icon: Users },
  { to: "/admin/zones", label: "Zones", icon: Map },
  { to: "/admin/rates", label: "Rate Cards", icon: CreditCard },
  { to: "/admin/notifications", label: "Notifications", icon: Bell },
];

const STATUSES = ["CREATED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED", "RESCHEDULED"];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  function load() {
    setError("");
    api.get("/orders").then((res) => setOrders(res.data)).catch((err) => setError(err.message));
  }
  useEffect(load, []);

  const filtered = useMemo(() => {
    if (!orders) return [];
    return orders.filter((o) => {
      const matchesSearch = !search || o.tracking_id.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = !statusFilter || o.current_status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [orders, search, statusFilter]);

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Admin">
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <h1 className="text-xl font-bold text-ink mb-1">Orders</h1>
        <p className="text-sm text-ink-muted mb-6">All shipments across the platform.</p>

        <div className="flex gap-3 mb-4">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
            <Input placeholder="Search tracking ID…" className="pl-8" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-48">
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </Select>
        </div>

        <Card>
          {!orders && !error && <LoadingState label="Loading orders" />}
          {error && <ErrorState message={error} onRetry={load} />}
          {orders && filtered.length === 0 && <EmptyState icon={Package} title="No matching orders" />}
          {orders && filtered.length > 0 && (
            <div className="divide-y divide-border">
              {filtered.map((o) => (
                <OrderRow key={o.id} order={o} expanded={expandedId === o.id} onToggle={() => setExpandedId(expandedId === o.id ? null : o.id)} onUpdated={load} />
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}

function OrderRow({ order, expanded, onToggle, onUpdated }) {
  const [agents, setAgents] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (expanded && !agents) {
      api.get("/agents").then((res) => setAgents(res.data)).catch(() => setAgents([]));
    }
  }, [expanded]);

  async function autoAssign() {
    setLoading(true);
    try {
      await api.post(`/orders/${order.id}/auto-assign`);
      toast.success(`${order.tracking_id} auto-assigned.`);
      onUpdated();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function manualAssign() {
    if (!selectedAgent) return;
    setLoading(true);
    try {
      await api.post(`/orders/${order.id}/assign`, { agent_id: selectedAgent });
      toast.success(`${order.tracking_id} assigned.`);
      onUpdated();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button onClick={onToggle} className="w-full flex items-center justify-between px-6 py-3.5 hover:bg-canvas transition-colors text-left">
        <div>
          <p className="text-sm font-mono font-semibold text-ink">{order.tracking_id}</p>
          <p className="text-xs text-ink-muted mt-0.5">{order.pickup_zone_name} → {order.drop_zone_name} · {order.order_type}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-mono text-ink">₹{order.total_charge.toFixed(2)}</span>
          <StatusBadge status={order.current_status} />
        </div>
      </button>

      {expanded && (
        <div className="px-6 pb-4 bg-canvas/50 border-t border-border">
          <div className="pt-4 flex flex-wrap items-end gap-3">
            <Button size="sm" variant="secondary" loading={loading} onClick={autoAssign}>Auto-assign</Button>
            <div className="flex items-end gap-2">
              <Select className="w-52" value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
                <option value="">Select agent…</option>
                {agents?.map((a) => <option key={a.id} value={a.id}>{a.full_name} ({a.current_zone_name})</option>)}
              </Select>
              <Button size="sm" variant="secondary" loading={loading} disabled={!selectedAgent} onClick={manualAssign}>Assign</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
