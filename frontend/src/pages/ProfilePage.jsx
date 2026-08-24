import { LayoutDashboard, Package, MapPin, Bell, User, Plus } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, Badge } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dashboard/new-shipment", label: "New Shipment", icon: Plus },
  { to: "/dashboard/orders", label: "My Orders", icon: Package },
  { to: "/dashboard/track", label: "Track", icon: MapPin },
  { to: "/dashboard/notifications", label: "Notifications", icon: Bell },
  { to: "/dashboard/profile", label: "Profile", icon: User },
];

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Customer">
      <div className="p-6 md:p-8 max-w-lg mx-auto">
        <h1 className="text-xl font-bold text-ink mb-6">Profile</h1>
        <Card className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xl font-semibold">
              {user?.full_name?.[0]?.toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-ink">{user?.full_name}</p>
              <Badge tone="brand">{user?.role}</Badge>
            </div>
          </div>
          <div className="space-y-4 text-sm">
            <Field label="Email" value={user?.email} />
            <Field label="Phone" value={user?.phone || "Not provided"} />
          </div>
        </Card>
      </div>
    </DashboardShell>
  );
}

function Field({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-ink-muted">{label}</span>
      <span className="text-ink font-medium">{value}</span>
    </div>
  );
}
