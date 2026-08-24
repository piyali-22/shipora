import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import AuthLayout from "../layouts/AuthLayout";
import Button from "../components/ui/Button";
import { Input, Label, FieldError } from "../components/ui/Input";

export default function RegisterPage() {
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      const user = await register({ ...form, phone: form.phone || undefined });
      toast.success("Account created. Welcome to Shipora!");
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout eyebrow="Create account" title="Get started with Shipora" subtitle="Set up your account to start booking shipments.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Full name</Label>
          <Input required placeholder="Priya Sharma" value={form.full_name} onChange={update("full_name")} />
        </div>
        <div>
          <Label>Email</Label>
          <Input type="email" required placeholder="you@company.in" value={form.email} onChange={update("email")} />
        </div>
        <div>
          <Label>Phone (optional)</Label>
          <Input placeholder="98XXXXXXXX" value={form.phone} onChange={update("phone")} />
        </div>
        <div>
          <Label>Password (min 8 characters)</Label>
          <Input type="password" required placeholder="••••••••" value={form.password} onChange={update("password")} />
        </div>
        <FieldError>{error}</FieldError>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-sm text-center text-ink-muted">
        Already registered?{" "}
        <Link to="/login" className="text-brand-600 font-medium hover:text-brand-700">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
