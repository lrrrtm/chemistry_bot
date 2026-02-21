import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    if (!token) {
      setIsAuthenticated(false);
      return;
    }
    api
      .verify()
      .then(() => setIsAuthenticated(true))
      .catch(() => {
        localStorage.removeItem("admin_token");
        setIsAuthenticated(false);
      });
  }, []);

  const login = async (password: string) => {
    const { token } = await api.login(password);
    localStorage.setItem("admin_token", token);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem("admin_token");
    setIsAuthenticated(false);
  };

  return { isAuthenticated, login, logout };
}
