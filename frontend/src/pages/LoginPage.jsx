import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth, dashboardPathForRole } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import AuthLayout from "../layouts/AuthLayout";
import Button from "../components/ui/Button";
import { Input, Label, FieldError } from "../components/ui/Input";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.full_name.split(" ")[0]}.`);
      navigate(dashboardPathForRole(user.role));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout eyebrow="Sign in" title="Welcome back" subtitle="Sign in to track, ship, and manage your deliveries.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Email</Label>
          <Input type="email" required placeholder="you@company.in" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <Label>Password</Label>
          <Input type="password" required placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <FieldError>{error}</FieldError>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Sign in
        </Button>
      </form>

      <div className="mt-6 flex flex-col gap-2 text-sm text-center">
        <p className="text-ink-muted">
          No account?{" "}
          <Link to="/register" className="text-brand-600 font-medium hover:text-brand-700">
            Create one
          </Link>
        </p>
        <Link to="/track" className="text-ink-muted hover:text-ink underline underline-offset-2">
          Track a shipment without signing in
        </Link>
      </div>
    </AuthLayout>
  );
}
