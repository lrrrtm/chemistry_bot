import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import logoImg from "@/assets/logo.png";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ThemeToggle } from "@/components/ThemeToggle";

export function LoginPage() {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryLoading, setRecoveryLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) return;
    setLoading(true);
    try {
      await login(password);
      navigate("/admin");
    } catch (err) {
      toast.error((err instanceof Error && err.message) ? err.message : "Неверный пароль");
    } finally {
      setLoading(false);
    }
  };

  const handleRecovery = async () => {
    setRecoveryLoading(true);
    try {
      await api.recoverPassword();
      toast.success("Новый пароль отправлен в Telegram");
      setShowRecovery(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка восстановления пароля");
    } finally {
      setRecoveryLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[var(--color-background)] p-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2">
            <img src={logoImg} alt="ХимБот" className="h-20 w-20" />
          </div>
          <CardTitle className="text-2xl">ХимБот</CardTitle>
          <CardDescription>Панель администратора</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Input
                id="password"
                type="password"
                placeholder="Введите пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Вход..." : "Войти"}
            </Button>
          </form>

          <div className="mt-4">
            {!showRecovery ? (
              <button
                type="button"
                onClick={() => setShowRecovery(true)}
                className="w-full text-sm text-center text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
              >
                Восстановить пароль
              </button>
            ) : (
              <div className="border rounded-md p-3 space-y-3 text-sm">
                <p className="text-[var(--color-muted-foreground)]">
                  Новый пароль будет сгенерирован и отправлен в Telegram администратора.
                </p>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => setShowRecovery(false)}
                    disabled={recoveryLoading}
                  >
                    Отмена
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    className="flex-1"
                    onClick={handleRecovery}
                    disabled={recoveryLoading}
                  >
                    {recoveryLoading ? "Отправка..." : "Подтвердить"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
