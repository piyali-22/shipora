import { useEffect, useState } from "react";
import { LayoutDashboard, Package, MapPin, Bell, User, Plus, Circle } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card } from "../components/ui/Card";
import { LoadingState, EmptyState, ErrorState } from "../components/ui/States";
import Button from "../components/ui/Button";
import api from "../lib/api";

function navItemsFor(role) {
  const base = role === "admin"
    ? [{ to: "/admin", label: "Overview", icon: LayoutDashboard }]
    : role === "agent"
    ? [{ to: "/agent", label: "Dashboard", icon: LayoutDashboard }]
    : [
        { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
        { to: "/dashboard/new-shipment", label: "New Shipment", icon: Plus },
        { to: "/dashboard/orders", label: "My Orders", icon: Package },
        { to: "/dashboard/track", label: "Track", icon: MapPin },
      ];
  return [...base, { to: "/dashboard/notifications", label: "Notifications", icon: Bell }, { to: "/dashboard/profile", label: "Profile", icon: User }];
}

export default function NotificationsPage({ role = "customer" }) {
  const [notifications, setNotifications] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    api.get("/notifications").then((res) => setNotifications(res.data)).catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function markAllRead() {
    try {
      await api.patch("/notifications/read-all");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function markRead(id) {
    await api.patch(`/notifications/${id}/read`).catch(() => {});
    load();
  }

  return (
    <DashboardShell navItems={navItemsFor(role)} roleLabel={role[0].toUpperCase() + role.slice(1)}>
      <div className="p-6 md:p-8 max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-ink">Notifications</h1>
          {notifications?.some((n) => !n.is_read) && (
            <Button variant="secondary" size="sm" onClick={markAllRead}>Mark all read</Button>
          )}
        </div>

        <Card>
          {!notifications && !error && <LoadingState label="Loading notifications" />}
          {error && <ErrorState message={error} onRetry={load} />}
          {notifications && notifications.length === 0 && (
            <EmptyState icon={Bell} title="No notifications yet" description="You'll see updates here whenever a shipment's status changes." />
          )}
          {notifications && notifications.length > 0 && (
            <div className="divide-y divide-border">
              {notifications.map((n) => (
                <button
                  key={n.id}
                  onClick={() => !n.is_read && markRead(n.id)}
                  className={`w-full text-left flex items-start gap-3 px-6 py-4 hover:bg-canvas transition-colors ${!n.is_read ? "bg-brand-50/30" : ""}`}
                >
                  {!n.is_read && <Circle size={7} className="fill-brand-600 text-brand-600 mt-1.5 shrink-0" />}
                  {n.is_read && <div className="w-[7px] shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-ink">{n.title}</p>
                    <p className="text-xs text-ink-muted mt-0.5">{n.message}</p>
                    <p className="text-[11px] text-ink-faint mt-1 font-mono">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}
