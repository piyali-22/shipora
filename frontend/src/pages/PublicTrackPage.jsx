import { useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import Button from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { StatusBadge } from "../components/ui/Card";
import { ErrorState, LoadingState } from "../components/ui/States";
import api from "../lib/api";

export default function PublicTrackPage() {
  const [trackingId, setTrackingId] = useState("");
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleTrack(e) {
    e.preventDefault();
    if (!trackingId.trim()) return;
    setLoading(true);
    setError("");
    setOrder(null);
    try {
      const res = await api.get(`/orders/track/${trackingId.trim().toUpperCase()}`);
      setOrder(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-canvas">
      <header className="h-16 flex items-center justify-between px-6 border-b border-border bg-white">
        <Link to="/" className="flex items-center gap-2">
          <img src="/shipora-icon.svg" alt="" className="w-6 h-6" />
          <span className="font-bold text-ink text-sm tracking-tight">SHIPORA</span>
        </Link>
        <Link to="/login">
          <Button variant="secondary" size="sm">Sign in</Button>
        </Link>
      </header>

      <div className="max-w-lg mx-auto px-6 py-16">
        <h1 className="text-2xl font-bold text-ink">Track your shipment</h1>
        <p className="text-sm text-ink-muted mt-1">Public tracking — no login required.</p>

        <form onSubmit={handleTrack} className="mt-6 flex gap-2">
          <Input
            placeholder="LM-XXXXXXX"
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
            className="font-mono uppercase"
          />
          <Button type="submit" loading={loading}>
            <Search size={16} /> Track
          </Button>
        </form>

        {error && <div className="mt-8"><ErrorState message={error} /></div>}
        {loading && <div className="mt-8"><LoadingState label="Looking up shipment" /></div>}

        {order && (
          <div className="mt-8 bg-white rounded-2xl border border-border shadow-card p-6">
            <div className="flex items-center justify-between">
              <span className="font-mono text-lg font-bold text-ink">{order.tracking_id}</span>
              <StatusBadge status={order.current_status} />
            </div>
            <div className="mt-4 text-sm text-ink-muted">
              {order.pickup_zone_name} → {order.drop_zone_name}
            </div>

            <div className="mt-6 space-y-4">
              {[...order.tracking_history].reverse().map((event, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center pt-1">
                    <div className={`w-2 h-2 rounded-full ${i === 0 ? "bg-brand-600" : "bg-slate-300"}`} />
                    {i < order.tracking_history.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
                  </div>
                  <div className="pb-4">
                    <p className="text-sm font-semibold text-ink">{event.status.replace(/_/g, " ")}</p>
                    <p className="text-xs text-ink-muted mt-0.5">
                      {new Date(event.timestamp).toLocaleString()} — {event.actor_name}
                    </p>
                    {event.note && <p className="text-xs text-ink-faint mt-1">{event.note}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
