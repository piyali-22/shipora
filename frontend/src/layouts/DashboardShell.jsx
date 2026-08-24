import { Link, useLocation } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function DashboardShell({ navItems, roleLabel, children }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-canvas flex">
      <aside className="hidden md:flex md:flex-col w-60 border-r border-border bg-white shrink-0">
        <div className="h-16 flex items-center gap-2 px-6 border-b border-border">
          <img src="/shipora-icon.svg" alt="" className="w-6 h-6" />
          <span className="font-bold text-ink tracking-tight text-sm">SHIPORA</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = location.pathname === item.to;
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                  ${active ? "bg-brand-50 text-brand-700" : "text-ink-muted hover:bg-canvas hover:text-ink"}`}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2.5 px-3 py-2">
            <div className="w-7 h-7 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-semibold shrink-0">
              {user?.full_name?.[0]?.toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-ink truncate">{user?.full_name}</p>
              <p className="text-[11px] text-ink-faint uppercase tracking-wide">{roleLabel}</p>
            </div>
            <button onClick={logout} className="text-ink-faint hover:text-danger shrink-0" title="Log out">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Mobile top bar */}
        <div className="md:hidden h-14 flex items-center justify-between px-4 border-b border-border bg-white">
          <div className="flex items-center gap-2">
            <img src="/shipora-icon.svg" alt="" className="w-6 h-6" />
            <span className="font-bold text-ink text-sm">SHIPORA</span>
          </div>
          <button onClick={logout} className="text-ink-faint">
            <LogOut size={16} />
          </button>
        </div>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
