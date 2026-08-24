import { useEffect, useState } from "react";
import { LayoutDashboard, MapPin, User } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, Badge, StatCard } from "../components/ui/Card";
import { LoadingState, ErrorState } from "../components/ui/States";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/agent", label: "Dashboard", icon: LayoutDashboard },
  { to: "/agent/track", label: "Track", icon: MapPin },
  { to: "/agent/profile", label: "Profile", icon: User },
];

export default function AgentProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/agents/me").then((res) => setProfile(res.data)).catch((err) => setError(err.message));
  }, []);

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Agent">
      <div className="p-6 md:p-8 max-w-lg mx-auto">
        <h1 className="text-xl font-bold text-ink mb-6">Profile</h1>

        {error && <ErrorState message={error} />}
        {!profile && !error && <LoadingState label="Loading profile" />}

        {profile && (
          <>
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xl font-semibold">
                  {user?.full_name?.[0]?.toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-ink">{user?.full_name}</p>
                  <Badge tone="brand">Agent · {profile.current_zone_name}</Badge>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-2 border-b border-border"><span className="text-ink-muted">Email</span><span className="text-ink font-medium">{user?.email}</span></div>
                <div className="flex justify-between py-2"><span className="text-ink-muted">Phone</span><span className="text-ink font-medium">{user?.phone || "Not provided"}</span></div>
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-4">
              <StatCard label="Active Deliveries" value={profile.active_assignment_count} accent="brand" />
              <StatCard label="Delivered" value={profile.total_deliveries_completed} accent="success" />
              <StatCard label="Failed" value={profile.total_deliveries_failed} accent="danger" />
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
