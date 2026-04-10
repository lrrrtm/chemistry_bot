import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  Plus,
  Users,
  Calculator,
  Database,
  BookPlus,
  Menu,
  X,
  LogOut,
  Tags,
  RotateCcw,
  Sun,
  Moon,
  FileText,
} from "lucide-react";
import logoImg from "@/assets/logo.png";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/admin/create-training", icon: Plus, label: "Создание тренировки" },
  { to: "/admin/students", icon: Users, label: "Ученики" },
  { to: "/admin/topics", icon: Tags, label: "Темы и теги" },
  { to: "/admin/theory-documents", icon: FileText, label: "Теория" },
  { to: "/admin/pool", icon: Database, label: "Пул вопросов" },
  { to: "/admin/add-question", icon: BookPlus, label: "Создание вопроса" },
  { to: "/admin/ege-converting", icon: Calculator, label: "Конвертация баллов" },
] as const;

type SidebarContentProps = {
  isDark: boolean;
  toggleTheme: () => void;
  onNavigate: () => void;
  onLogout: () => void;
};

function SidebarContent({ isDark, toggleTheme, onNavigate, onLogout }: SidebarContentProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-[var(--color-sidebar-muted)] px-4 py-5">
        <img src={logoImg} alt="ХимБот" className="h-8 w-8 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-[var(--color-sidebar-foreground)]">ХимБот</p>
          <p className="text-xs text-[var(--color-sidebar-foreground)] opacity-60">Администратор</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
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

      <div className="space-y-1 border-t border-[var(--color-sidebar-muted)] p-3">
        <button
          onClick={toggleTheme}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-[var(--color-sidebar-foreground)] transition-colors hover:bg-[var(--color-sidebar-muted)]"
        >
          {isDark ? <Sun className="h-4 w-4 shrink-0" /> : <Moon className="h-4 w-4 shrink-0" />}
          {isDark ? "Светлая тема" : "Тёмная тема"}
        </button>
        <NavLink
          to="/admin/restore"
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
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
          className="h-auto w-full justify-start gap-3 px-3 py-2.5 text-sm font-medium text-[var(--color-sidebar-foreground)] hover:bg-[var(--color-sidebar-muted)] hover:text-[var(--color-sidebar-foreground)]"
          onClick={onLogout}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Выйти
        </Button>
      </div>
    </div>
  );
}

export function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isDark, toggle: toggleTheme } = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-background)]">
      <aside className="hidden w-64 shrink-0 flex-col bg-[var(--color-sidebar)] md:flex">
        <SidebarContent
          isDark={isDark}
          toggleTheme={toggleTheme}
          onNavigate={closeSidebar}
          onLogout={handleLogout}
        />
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 md:hidden" onClick={closeSidebar} />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[var(--color-sidebar)] transition-transform duration-200 md:hidden",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent
          isDark={isDark}
          toggleTheme={toggleTheme}
          onNavigate={closeSidebar}
          onLogout={handleLogout}
        />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="shrink-0 border-b bg-[var(--color-card)] px-2 py-1 md:hidden">
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setSidebarOpen(open => !open)}>
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
