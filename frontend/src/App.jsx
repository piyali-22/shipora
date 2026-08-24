import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth, dashboardPathForRole } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PublicTrackPage from "./pages/PublicTrackPage";

import CustomerDashboardPage from "./pages/CustomerDashboardPage";
import NewShipmentPage from "./pages/NewShipmentPage";
import MyOrdersPage from "./pages/MyOrdersPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import DashboardTrackPage from "./pages/DashboardTrackPage";
import NotificationsPage from "./pages/NotificationsPage";
import ProfilePage from "./pages/ProfilePage";

import AgentDashboardPage from "./pages/AgentDashboardPage";
import AgentTrackPage from "./pages/AgentTrackPage";
import AgentProfilePage from "./pages/AgentProfilePage";

import AdminDashboardPage from "./pages/AdminDashboardPage";
import AdminOrdersPage from "./pages/AdminOrdersPage";
import AdminZonesPage from "./pages/AdminZonesPage";
import AdminRateCardsPage from "./pages/AdminRateCardsPage";
import AdminAgentsPage from "./pages/AdminAgentsPage";

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={dashboardPathForRole(user.role)} replace />;
}

function Protected({ role, children }) {
  return <ProtectedRoute allowedRoles={[role]}>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/" element={<RootRedirect />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/track" element={<PublicTrackPage />} />

            {/* Customer */}
            <Route path="/dashboard" element={<Protected role="customer"><CustomerDashboardPage /></Protected>} />
            <Route path="/dashboard/new-shipment" element={<Protected role="customer"><NewShipmentPage /></Protected>} />
            <Route path="/dashboard/orders" element={<Protected role="customer"><MyOrdersPage /></Protected>} />
            <Route path="/dashboard/orders/:orderId" element={<Protected role="customer"><OrderDetailPage /></Protected>} />
            <Route path="/dashboard/track" element={<Protected role="customer"><DashboardTrackPage /></Protected>} />
            <Route path="/dashboard/notifications" element={<Protected role="customer"><NotificationsPage role="customer" /></Protected>} />
            <Route path="/dashboard/profile" element={<Protected role="customer"><ProfilePage /></Protected>} />

            {/* Agent */}
            <Route path="/agent" element={<Protected role="agent"><AgentDashboardPage /></Protected>} />
            <Route path="/agent/track" element={<Protected role="agent"><AgentTrackPage /></Protected>} />
            <Route path="/agent/profile" element={<Protected role="agent"><AgentProfilePage /></Protected>} />

            {/* Admin */}
            <Route path="/admin" element={<Protected role="admin"><AdminDashboardPage /></Protected>} />
            <Route path="/admin/orders" element={<Protected role="admin"><AdminOrdersPage /></Protected>} />
            <Route path="/admin/zones" element={<Protected role="admin"><AdminZonesPage /></Protected>} />
            <Route path="/admin/rates" element={<Protected role="admin"><AdminRateCardsPage /></Protected>} />
            <Route path="/admin/agents" element={<Protected role="admin"><AdminAgentsPage /></Protected>} />
            <Route path="/admin/notifications" element={<Protected role="admin"><NotificationsPage role="admin" /></Protected>} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
