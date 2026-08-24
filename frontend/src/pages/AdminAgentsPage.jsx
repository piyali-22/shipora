import { useEffect, useState } from "react";
import { LayoutDashboard, Package, Users, Map, CreditCard, Bell, Plus } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, Badge } from "../components/ui/Card";
import { Input, Label, Select } from "../components/ui/Input";
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

export default function AdminAgentsPage() {
  const [agents, setAgents] = useState(null);
  const [zones, setZones] = useState([]);
  const [error, setError] = useState("");
  const [accountForm, setAccountForm] = useState({ full_name: "", email: "", password: "" });
  const [profileForm, setProfileForm] = useState({ agent_email: "", zone_id: "" });
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [creatingProfile, setCreatingProfile] = useState(false);
  const toast = useToast();

  function load() {
    setError("");
    Promise.all([api.get("/agents"), api.get("/zones")])
      .then(([a, z]) => { setAgents(a.data); setZones(z.data); })
      .catch((err) => setError(err.message));
  }
  useEffect(load, []);

  async function handleCreateAccount(e) {
    e.preventDefault();
    setCreatingAccount(true);
    try {
      await api.post("/auth/admin/create", { ...accountForm, role: "agent" });
      toast.success(`Agent account created for ${accountForm.email}. Now create their profile below.`);
      setProfileForm((f) => ({ ...f, agent_email: accountForm.email }));
      setAccountForm({ full_name: "", email: "", password: "" });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setCreatingAccount(false);
    }
  }

  async function handleCreateProfile(e) {
    e.preventDefault();
    setCreatingProfile(true);
    try {
      await api.post("/agents", profileForm);
      toast.success("Agent profile created.");
      setProfileForm({ agent_email: "", zone_id: "" });
      load();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setCreatingProfile(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Admin">
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <h1 className="text-xl font-bold text-ink mb-1">Agents</h1>
        <p className="text-sm text-ink-muted mb-6">Delivery agent accounts and zone assignments.</p>

        <div className="grid lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            {!agents && !error && <LoadingState label="Loading agents" />}
            {error && <ErrorState message={error} onRetry={load} />}
            {agents && agents.length === 0 && <EmptyState icon={Users} title="No agents yet" description="Create an agent account, then set up their profile." />}
            {agents && agents.length > 0 && (
              <div className="divide-y divide-border">
                {agents.map((a) => (
                  <div key={a.id} className="flex items-center justify-between px-6 py-4">
                    <div>
                      <p className="text-sm font-semibold text-ink">{a.full_name}</p>
                      <p className="text-xs text-ink-muted mt-0.5">{a.email} · {a.current_zone_name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={a.is_available ? "success" : "default"}>{a.is_available ? "Available" : "Unavailable"}</Badge>
                      <span className="text-xs font-mono text-ink-muted">Load: {a.active_assignment_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <div className="space-y-6">
            <Card className="p-5">
              <h3 className="text-sm font-semibold text-ink mb-4">1. Create Agent Account</h3>
              <form onSubmit={handleCreateAccount} className="space-y-3">
                <div><Label>Full name</Label><Input required value={accountForm.full_name} onChange={(e) => setAccountForm((f) => ({ ...f, full_name: e.target.value }))} /></div>
                <div><Label>Email</Label><Input required type="email" value={accountForm.email} onChange={(e) => setAccountForm((f) => ({ ...f, email: e.target.value }))} /></div>
                <div><Label>Temp password</Label><Input required type="password" value={accountForm.password} onChange={(e) => setAccountForm((f) => ({ ...f, password: e.target.value }))} /></div>
                <Button type="submit" size="sm" className="w-full" loading={creatingAccount}>Create Account</Button>
              </form>
            </Card>

            <Card className="p-5">
              <h3 className="text-sm font-semibold text-ink mb-4">2. Create Agent Profile</h3>
              <form onSubmit={handleCreateProfile} className="space-y-3">
                <div><Label>Agent email</Label><Input required type="email" value={profileForm.agent_email} onChange={(e) => setProfileForm((f) => ({ ...f, agent_email: e.target.value }))} /></div>
                <div>
                  <Label>Zone</Label>
                  <Select required value={profileForm.zone_id} onChange={(e) => setProfileForm((f) => ({ ...f, zone_id: e.target.value }))}>
                    <option value="">Select zone…</option>
                    {zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}
                  </Select>
                </div>
                <Button type="submit" size="sm" className="w-full" loading={creatingProfile}><Plus size={14} /> Create Profile</Button>
              </form>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
