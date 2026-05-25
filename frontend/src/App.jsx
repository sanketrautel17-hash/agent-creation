import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthPage from "./pages/AuthPage";
import AgentPage from "./pages/AgentPage";
import BulkCallsPage from "./pages/BulkCallsPage";
import DashboardPage from "./pages/DashboardPage";
import SignupPage from "./pages/SignupPage";

function AppShell() {
  const location = useLocation();
  const isDoctorWorkspaceRoute =
    location.pathname === "/dashboard" ||
    location.pathname.startsWith("/agents/") ||
    location.pathname === "/campaigns" ||
    location.pathname === "/" ||
    location.pathname === "/login" ||
    location.pathname === "/signup" ||
    location.pathname === "/admin/login" ||
    location.pathname === "/invite/accept" ||
    location.pathname === "/otp";

  return (
    <div className="app-shell">
      {isDoctorWorkspaceRoute ? null : <Navbar />}
      <main className={`page-shell ${isDoctorWorkspaceRoute ? "page-shell-doctor" : ""}`}>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/admin/login" element={<Navigate to="/login" replace />} />
          <Route path="/invite/accept" element={<SignupPage />} />
          <Route path="/otp" element={<AuthPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns"
            element={
              <ProtectedRoute>
                <BulkCallsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/agents/:agentId"
            element={
              <ProtectedRoute>
                <AgentPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const { loading } = useAuth();

  if (loading) {
    return <div className="center-card">Restoring your session...</div>;
  }

  return <AppShell />;
}
