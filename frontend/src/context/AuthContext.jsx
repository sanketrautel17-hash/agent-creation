import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { authService } from "../services/authService";
import { apiClient, setAccessToken } from "../services/api";

const AuthContext = createContext(null);

const ACCESS_TOKEN_KEY = "doctor_ai_access_token";
const USER_KEY = "doctor_ai_user";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });
  const [token, setTokenState] = useState(() => localStorage.getItem(ACCESS_TOKEN_KEY));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAccessToken(token);
  }, [token]);

  useEffect(() => {
    const restoreSession = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        setAccessToken(token);
        const profile = await authService.me();
        setUser(profile);
        localStorage.setItem(USER_KEY, JSON.stringify(profile));
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = ({ access_token, user: nextUser }) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
    setTokenState(access_token);
    setUser(nextUser);
    setAccessToken(access_token);
  };

  const logout = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setTokenState(null);
    setUser(null);
    setAccessToken(null);
  };

  const value = useMemo(
    () => ({
      apiClient,
      loading,
      token,
      user,
      login,
      logout,
      isAuthenticated: Boolean(token && user),
      isAdmin: user?.role === "admin",
    }),
    [loading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
