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

const EMPTY_FORM = {
  name: "", order_type: "B2C", scope: "INTRA_ZONE",
  base_charge: "", included_kg: "1", per_extra_kg_charge: "",
  cod_flat_charge: "0", cod_percent_of_subtotal: "0",
};

export default function AdminRateCardsPage() {
  const [rates, setRates] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [creating, setCreating] = useState(false);
  const toast = useToast();

  function load() {
    setError("");
    api.get("/rates").then((res) => setRates(res.data)).catch((err) => setError(err.message));
  }
  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/rates", {
        ...form,
        base_charge: Number(form.base_charge),
        included_kg: Number(form.included_kg),
        per_extra_kg_charge: Number(form.per_extra_kg_charge),
        cod_flat_charge: Number(form.cod_flat_charge),
        cod_percent_of_subtotal: Number(form.cod_percent_of_subtotal),
      });
      toast.success(`Rate card "${form.name}" created and activated.`);
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Admin">
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        <h1 className="text-xl font-bold text-ink mb-1">Rate Cards</h1>
        <p className="text-sm text-ink-muted mb-6">Pricing engine config — versioned, edits never alter historical orders.</p>

        <div className="grid lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 overflow-x-auto">
            {!rates && !error && <LoadingState label="Loading rate cards" />}
            {error && <ErrorState message={error} onRetry={load} />}
            {rates && rates.length === 0 && <EmptyState icon={CreditCard} title="No rate cards yet" description="Pricing can't be calculated until at least one rate card exists." />}
            {rates && rates.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-ink-muted uppercase tracking-wide border-b border-border">
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-3 py-3 font-medium">Type</th>
                    <th className="px-3 py-3 font-medium">Scope</th>
                    <th className="px-3 py-3 font-medium">Base</th>
                    <th className="px-3 py-3 font-medium">Per KG</th>
                    <th className="px-3 py-3 font-medium">Ver</th>
                    <th className="px-3 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono text-xs">
                  {rates.map((r) => (
                    <tr key={r.id}>
                      <td className="px-5 py-3 font-sans text-ink">{r.name}</td>
                      <td className="px-3 py-3">{r.order_type}</td>
                      <td className="px-3 py-3">{r.scope.replace("_ZONE", "")}</td>
                      <td className="px-3 py-3">₹{r.base_charge}</td>
                      <td className="px-3 py-3">₹{r.per_extra_kg_charge}</td>
                      <td className="px-3 py-3">V{r.version}</td>
                      <td className="px-3 py-3"><Badge tone={r.is_active ? "success" : "default"}>{r.is_active ? "Active" : "Old"}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          <Card className="p-5 h-fit">
            <h3 className="text-sm font-semibold text-ink mb-4">New Rate Card</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div><Label>Name</Label><Input required value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></div>
              <div className="grid grid-cols-2 gap-2">
                <div><Label>Order Type</Label><Select value={form.order_type} onChange={(e) => setForm((f) => ({ ...f, order_type: e.target.value }))}><option>B2C</option><option>B2B</option></Select></div>
                <div><Label>Scope</Label><Select value={form.scope} onChange={(e) => setForm((f) => ({ ...f, scope: e.target.value }))}><option value="INTRA_ZONE">Intra-zone</option><option value="INTER_ZONE">Inter-zone</option></Select></div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div><Label>Base ₹</Label><Input required type="number" value={form.base_charge} onChange={(e) => setForm((f) => ({ ...f, base_charge: e.target.value }))} /></div>
                <div><Label>Included KG</Label><Input required type="number" value={form.included_kg} onChange={(e) => setForm((f) => ({ ...f, included_kg: e.target.value }))} /></div>
              </div>
              <div><Label>Per Extra KG ₹</Label><Input required type="number" value={form.per_extra_kg_charge} onChange={(e) => setForm((f) => ({ ...f, per_extra_kg_charge: e.target.value }))} /></div>
              <div className="grid grid-cols-2 gap-2">
                <div><Label>COD Flat ₹</Label><Input type="number" value={form.cod_flat_charge} onChange={(e) => setForm((f) => ({ ...f, cod_flat_charge: e.target.value }))} /></div>
                <div><Label>COD %</Label><Input type="number" value={form.cod_percent_of_subtotal} onChange={(e) => setForm((f) => ({ ...f, cod_percent_of_subtotal: e.target.value }))} /></div>
              </div>
              <Button type="submit" className="w-full" loading={creating}><Plus size={14} /> Create Card</Button>
            </form>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
