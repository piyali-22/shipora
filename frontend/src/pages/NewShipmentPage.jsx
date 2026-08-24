import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, MapPin, Bell, User, Plus, Loader2 } from "lucide-react";
import DashboardShell from "../layouts/DashboardShell";
import { Card } from "../components/ui/Card";
import Button from "../components/ui/Button";
import { Input, Label, Textarea, FieldError } from "../components/ui/Input";
import { useToast } from "../context/ToastContext";
import api from "../lib/api";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dashboard/new-shipment", label: "New Shipment", icon: Plus },
  { to: "/dashboard/orders", label: "My Orders", icon: Package },
  { to: "/dashboard/track", label: "Track", icon: MapPin },
  { to: "/dashboard/notifications", label: "Notifications", icon: Bell },
  { to: "/dashboard/profile", label: "Profile", icon: User },
];

const EMPTY_FORM = {
  pickup_address: "",
  drop_address: "",
  length_cm: "",
  breadth_cm: "",
  height_cm: "",
  actual_weight_kg: "",
  order_type: "B2C",
  payment_type: "PREPAID",
};

export default function NewShipmentPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [quote, setQuote] = useState(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState("");
  const [confirming, setConfirming] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  const isComplete = useMemo(() => {
    return (
      form.pickup_address.trim().length > 8 &&
      form.drop_address.trim().length > 8 &&
      Number(form.length_cm) > 0 &&
      Number(form.breadth_cm) > 0 &&
      Number(form.height_cm) > 0 &&
      Number(form.actual_weight_kg) > 0
    );
  }, [form]);

  // Debounced live quote — fetch a fresh price ~500ms after the user
  // stops typing/changing anything, mirroring the "live manifest" idea.
  useEffect(() => {
    if (!isComplete) {
      setQuote(null);
      setQuoteError("");
      return;
    }
    setQuoteLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await api.post("/orders/quote", {
          ...form,
          length_cm: Number(form.length_cm),
          breadth_cm: Number(form.breadth_cm),
          height_cm: Number(form.height_cm),
          actual_weight_kg: Number(form.actual_weight_kg),
        });
        setQuote(res.data);
        setQuoteError("");
      } catch (err) {
        setQuote(null);
        setQuoteError(err.message);
      } finally {
        setQuoteLoading(false);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [form, isComplete]);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleConfirm() {
    setConfirming(true);
    try {
      const res = await api.post("/orders", {
        ...form,
        length_cm: Number(form.length_cm),
        breadth_cm: Number(form.breadth_cm),
        height_cm: Number(form.height_cm),
        actual_weight_kg: Number(form.actual_weight_kg),
      });
      toast.success(`Shipment confirmed — tracking ID ${res.data.tracking_id}`);
      navigate(`/dashboard/orders/${res.data.id}`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setConfirming(false);
    }
  }

  return (
    <DashboardShell navItems={NAV_ITEMS} roleLabel="Customer">
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <h1 className="text-xl font-bold text-ink">New Shipment</h1>
        <p className="text-sm text-ink-muted mt-0.5">Order creation with a live price estimate.</p>

        <div className="mt-6 grid lg:grid-cols-3 gap-6">
          {/* Form */}
          <Card className="lg:col-span-2 p-6 space-y-5">
            <div>
              <Label>Pickup address</Label>
              <Textarea
                rows={2}
                placeholder="Flat, street, area, city — include 6-digit PIN"
                value={form.pickup_address}
                onChange={update("pickup_address")}
              />
            </div>
            <div>
              <Label>Drop address</Label>
              <Textarea
                rows={2}
                placeholder="Flat, street, area, city — include 6-digit PIN"
                value={form.drop_address}
                onChange={update("drop_address")}
              />
            </div>

            <div>
              <Label>Package dimensions (cm)</Label>
              <div className="grid grid-cols-3 gap-3">
                <Input type="number" min="0" placeholder="Length" value={form.length_cm} onChange={update("length_cm")} />
                <Input type="number" min="0" placeholder="Breadth" value={form.breadth_cm} onChange={update("breadth_cm")} />
                <Input type="number" min="0" placeholder="Height" value={form.height_cm} onChange={update("height_cm")} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Actual weight (kg)</Label>
                <Input type="number" min="0" step="0.1" placeholder="0.00" value={form.actual_weight_kg} onChange={update("actual_weight_kg")} />
              </div>
              <div>
                <Label>Order type</Label>
                <ToggleGroup
                  options={[{ value: "B2B", label: "B2B" }, { value: "B2C", label: "B2C" }]}
                  value={form.order_type}
                  onChange={(v) => setForm((f) => ({ ...f, order_type: v }))}
                />
              </div>
            </div>

            <div>
              <Label>Payment type</Label>
              <ToggleGroup
                options={[{ value: "PREPAID", label: "Prepaid" }, { value: "COD", label: "COD" }]}
                value={form.payment_type}
                onChange={(v) => setForm((f) => ({ ...f, payment_type: v }))}
              />
            </div>
          </Card>

          {/* Live manifest / price panel */}
          <div className="lg:sticky lg:top-6 h-fit">
            <Card className="overflow-hidden">
              <div className="px-5 py-3.5 border-b border-border flex items-center justify-between bg-canvas">
                <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Manifest</span>
                {quoteLoading && <Loader2 size={13} className="animate-spin text-ink-faint" />}
                {!quoteLoading && quote && <span className="text-[10px] font-mono text-success">LIVE</span>}
              </div>

              <div className="px-5 py-4 font-mono text-xs space-y-2.5">
                {!isComplete && (
                  <p className="text-ink-faint font-sans text-sm py-6 text-center">
                    Fill in the shipment details to see a live price.
                  </p>
                )}

                {isComplete && quoteError && (
                  <p className="text-danger font-sans text-sm py-4">{quoteError}</p>
                )}

                {isComplete && quote && (
                  <>
                    <ManifestRow label="ROUTE" value={`${quote.pickup_zone.code} → ${quote.drop_zone.code}`} />
                    <ManifestRow label="ZONE TYPE" value={quote.zone_type.replace("_", " ")} />
                    <ManifestRow label="ACTUAL WT" value={`${quote.actual_weight} KG`} />
                    <ManifestRow label="VOLUMETRIC WT" value={`${quote.volumetric_weight} KG`} highlight />
                    <ManifestRow label="BILLED WT" value={`${quote.chargeable_weight} KG`} bold />
                    <div className="h-px bg-border my-3" />
                    <ManifestRow label="BASE CHARGE" value={`₹${quote.base_charge.toFixed(2)}`} />
                    <ManifestRow label="WEIGHT CHG" value={`₹${quote.extra_weight_charge.toFixed(2)}`} />
                    {quote.cod_surcharge > 0 && (
                      <ManifestRow label="COD SURCHARGE" value={`₹${quote.cod_surcharge.toFixed(2)}`} />
                    )}
                    <div className="h-px bg-border my-3" />
                    <div className="flex items-baseline justify-between">
                      <span className="font-sans text-sm font-semibold text-ink">Total</span>
                      <span className="text-xl font-bold text-brand-600">₹{quote.total.toFixed(2)}</span>
                    </div>
                  </>
                )}
              </div>

              <div className="p-4 border-t border-border">
                <Button className="w-full" size="lg" disabled={!quote || quoteLoading} loading={confirming} onClick={handleConfirm}>
                  Confirm Shipment
                </Button>
                {!quote && isComplete && !quoteLoading && !quoteError && (
                  <p className="text-xs text-ink-faint text-center mt-2">Calculating price…</p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}

function ManifestRow({ label, value, highlight, bold }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-faint">{label}</span>
      <span className={`${bold ? "font-bold text-ink" : highlight ? "text-brand-600" : "text-ink-muted"}`}>
        {value}
      </span>
    </div>
  );
}

function ToggleGroup({ options, value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={`h-10 rounded-lg text-sm font-medium border transition-colors
            ${value === opt.value ? "bg-brand-600 text-white border-brand-600" : "bg-white text-ink-muted border-border hover:border-border-strong"}`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
