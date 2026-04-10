import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { ThemeToggle } from "@/components/ThemeToggle";
import { type WorkDetail, WorkSummaryCard, QuestionsList } from "@/components/WorkStatsView";
import logoImg from "@/assets/logo.png";

export function StudentViewStats() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [stats, setStats] = useState<WorkDetail | null>(null);
  const [error, setError] = useState<string | null>(token ? null : "Неверная ссылка");
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      return;
    }

    api.getWorkStats(token)
      .then((data) => {
        setStats(data);
        document.title = `${data.general.name} — ХимБот`;
      })
      .catch(() => setError("Тренировка не найдена или ссылка недействительна"))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <header className="sticky top-0 z-10 border-b bg-[var(--color-card)]">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <img src={logoImg} alt="ХимБот" className="h-5 w-5" />
            <span className="font-semibold">ХимБот</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-2xl space-y-5 px-4 py-6">
        {loading && (
          <div className="py-16 text-center text-[var(--color-muted-foreground)]">
            <img src={logoImg} alt="" className="mx-auto mb-3 h-10 w-10 animate-pulse opacity-30" />
            <p>Загружаем результаты...</p>
          </div>
        )}

        {error && (
          <Card className="border-[var(--color-destructive)]">
            <CardContent className="py-6 text-center text-[var(--color-destructive)]">
              <p>{error}</p>
            </CardContent>
          </Card>
        )}

        {stats && (
          <>
            <WorkSummaryCard general={stats.general} userName />
            <QuestionsList questions={stats.questions} answerLabel="Твой ответ" />
          </>
        )}
      </main>
    </div>
  );
}
