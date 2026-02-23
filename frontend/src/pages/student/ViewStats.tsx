import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FlaskConical } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { ThemeToggle } from "@/components/ThemeToggle";
import { type WorkDetail, WorkSummaryCard, QuestionsList } from "@/components/WorkStatsView";

export function StudentViewStats() {
  const [params] = useSearchParams();
  const [stats, setStats] = useState<WorkDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = params.get("token");

    if (!token) {
      setError("Неверная ссылка");
      setLoading(false);
      return;
    }

    api.getWorkStats(token)
      .then(setStats)
      .catch(() => setError("Тренировка не найдена или ссылка недействительна"))
      .finally(() => setLoading(false));
  }, [params]);

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <header className="border-b bg-[var(--color-card)] sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-[var(--color-primary)]" />
            <span className="font-semibold">ХимБот</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {loading && (
          <div className="text-center py-16 text-[var(--color-muted-foreground)]">
            <FlaskConical className="h-10 w-10 mx-auto mb-3 opacity-30 animate-pulse" />
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
