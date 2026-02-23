import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  Plus, Users, Calculator, Database, BookPlus, Menu, X, LogOut, Tags, RotateCcw,
} from "lucide-react";
import logoImg from "@/assets/logo.png";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/admin/create-training", icon: Plus, label: "Создание тренировки" },
  { to: "/admin/students", icon: Users, label: "Ученики" },
  { to: "/admin/topics", icon: Tags, label: "Темы и теги" },
  { to: "/admin/pool", icon: Database, label: "Пул вопросов" },
  { to: "/admin/add-question", icon: BookPlus, label: "Создание вопроса" },
  { to: "/admin/ege-converting", icon: Calculator, label: "Конвертация баллов" },
];

export function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-5 border-b border-[var(--color-sidebar-muted)]">
        <img src={logoImg} alt="ХимБот" className="h-8 w-8 shrink-0" />
        <div>
          <p className="font-semibold text-[var(--color-sidebar-foreground)] text-sm">ХимБот</p>
          <p className="text-xs text-[var(--color-sidebar-foreground)] opacity-60">Администратор</p>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--color-primary)] text-white"
                  : "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)]"
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-[var(--color-sidebar-muted)] space-y-1">
        <NavLink
          to="/admin/restore"
          onClick={() => setSidebarOpen(false)}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              isActive
                ? "bg-[var(--color-primary)] text-white"
                : "text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)]"
            )
          }
        >
          <RotateCcw className="h-4 w-4 shrink-0" />
          Восстановление
        </NavLink>
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 px-3 py-2.5 h-auto text-sm font-medium text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] hover:text-[var(--color-sidebar-foreground)]"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Выйти
        </Button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[var(--color-background)] overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 flex-col bg-[var(--color-sidebar)] shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 flex flex-col bg-[var(--color-sidebar)] transform transition-transform duration-200 md:hidden",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 py-5 border-b bg-[var(--color-card)] shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          <div className="hidden md:block" />
          <div className="flex items-center gap-2 ml-auto">
            <ThemeToggle />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
