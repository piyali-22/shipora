import { useEffect, useState } from "react";
import { LayoutDashboard, Package, Users, Map, CreditCard, Bell, Plus } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card, Badge } from "../components/ui/Card";
import { Input, Label } from "../components/ui/Input";
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

export default function AdminZonesPage() {
  const [zones, setZones] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", code: "", pincodes: "" });
  const [creating, setCreating] = useState(false);
  const toast = useToast();

  function load() {
    setError("");
    api.get("/zones").then((res) => setZones(res.data)).catch((err) => setError(err.message));
  }
  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    try {
      const pincodes = form.pincodes.split(",").map((p) => p.trim()).filter(Boolean);
      await api.post("/zones", { name: form.name, code: form.code, pincodes });
      toast.success(`Zone "${form.name}" created.`);
      setForm({ name: "", code: "", pincodes: "" });
      load();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Admin">
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <h1 className="text-xl font-bold text-ink mb-1">Zones</h1>
        <p className="text-sm text-ink-muted mb-6">Delivery zones and PIN code mappings.</p>

        <div className="grid lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            {!zones && !error && <LoadingState label="Loading zones" />}
            {error && <ErrorState message={error} onRetry={load} />}
            {zones && zones.length === 0 && <EmptyState icon={Map} title="No zones yet" description="Create your first zone to start resolving addresses." />}
            {zones && zones.length > 0 && (
              <div className="divide-y divide-border">
                {zones.map((z) => (
                  <div key={z.id} className="flex items-center justify-between px-6 py-4">
                    <div>
                      <p className="text-sm font-semibold text-ink">{z.name} <span className="text-ink-faint font-mono text-xs">({z.code})</span></p>
                      <p className="text-xs text-ink-muted mt-1">{z.pincode_count} PIN code{z.pincode_count !== 1 ? "s" : ""}</p>
                    </div>
                    <Badge tone={z.is_active ? "success" : "default"}>{z.is_active ? "Active" : "Inactive"}</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-5 h-fit">
            <h3 className="text-sm font-semibold text-ink mb-4">New Zone</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <Label>Name</Label>
                <Input required placeholder="Delhi NCR" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <Label>Code</Label>
                <Input required placeholder="ZN-NCR" value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))} />
              </div>
              <div>
                <Label>PIN codes (comma-separated)</Label>
                <Input placeholder="110001, 110005" value={form.pincodes} onChange={(e) => setForm((f) => ({ ...f, pincodes: e.target.value }))} />
              </div>
              <Button type="submit" className="w-full" loading={creating}><Plus size={14} /> Create Zone</Button>
            </form>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
