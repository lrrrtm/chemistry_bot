import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FlaskConical, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ThemeToggle";

type WorkStats = {
  general: {
    user_name: string | null;
    name: string;
    start: string | null;
    end: string | null;
    final_mark: number;
    max_mark: number;
    fully: number;
    semi: number;
    zero: number;
  };
  questions: Array<{
    index: number;
    question_id: number;
    text: string;
    answer: string;
    user_answer: string;
    user_mark: number;
    full_mark: number;
    question_image: boolean;
    answer_image: boolean;
  }>;
  detailed: boolean;
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function formatDuration(start: string | null, end: string | null) {
  if (!start || !end) return "—";
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  if (h > 0) return `${h}ч ${m}м ${s}с`;
  if (m > 0) return `${m}м ${s}с`;
  return `${s}с`;
}

function getResultColor(mark: number, fullMark: number) {
  if (mark === fullMark) return "text-green-600 dark:text-green-400";
  if (mark > 0) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-500 dark:text-red-400";
}

function ResultBadge({ mark, fullMark }: { mark: number; fullMark: number }) {
  if (mark === fullMark) return <Badge variant="success">Верно</Badge>;
  if (mark > 0) return <Badge variant="warning">Частично</Badge>;
  return <Badge variant="destructive">Неверно</Badge>;
}

export function StudentViewStats() {
  const [params] = useSearchParams();
  const [stats, setStats] = useState<WorkStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const uuid = params.get("uuid");
    const tid = params.get("tid");
    const work = params.get("work");
    const detailed = params.get("detailed") === "1" ? 1 : 0;

    if (!uuid || !tid || !work) {
      setError("Неверная ссылка");
      setLoading(false);
      return;
    }

    api.getStudentWorkStats(uuid, tid, work, detailed)
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
            {/* General info */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{stats.general.name}</CardTitle>
                {stats.general.user_name && (
                  <p className="text-sm text-[var(--color-muted-foreground)]">
                    Ученик: {stats.general.user_name}
                  </p>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-[var(--color-primary)]">
                      {stats.general.final_mark}
                    </p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">
                      из {stats.general.max_mark} баллов
                    </p>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-center gap-1 text-lg font-semibold">
                      <span className="text-green-600">{stats.general.fully}</span>
                      <span className="text-yellow-500">{stats.general.semi}</span>
                      <span className="text-red-500">{stats.general.zero}</span>
                    </div>
                    <p className="text-xs text-[var(--color-muted-foreground)]">вер / частич / нет</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      {formatDuration(stats.general.start, stats.general.end)}
                    </p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">времени затрачено</p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex rounded-full overflow-hidden h-3">
                    {stats.general.fully > 0 && (
                      <div
                        className="bg-green-500"
                        style={{ width: `${(stats.general.fully / (stats.general.fully + stats.general.semi + stats.general.zero)) * 100}%` }}
                      />
                    )}
                    {stats.general.semi > 0 && (
                      <div
                        className="bg-yellow-500"
                        style={{ width: `${(stats.general.semi / (stats.general.fully + stats.general.semi + stats.general.zero)) * 100}%` }}
                      />
                    )}
                    {stats.general.zero > 0 && (
                      <div
                        className="bg-red-500"
                        style={{ width: `${(stats.general.zero / (stats.general.fully + stats.general.semi + stats.general.zero)) * 100}%` }}
                      />
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-muted-foreground)] text-right">
                    Завершено: {formatDate(stats.general.end)}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Questions */}
            <div className="space-y-3">
              <h2 className="font-semibold text-lg flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Подробности
              </h2>

              {stats.questions.map((q) => (
                <Card
                  key={q.question_id}
                  className={`border-l-4 ${
                    q.user_mark === q.full_mark
                      ? "border-l-green-500"
                      : q.user_mark > 0
                      ? "border-l-yellow-500"
                      : "border-l-red-500"
                  }`}
                >
                  <CardContent className="pt-4 space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-[var(--color-muted-foreground)]">
                        Вопрос №{q.index} (id{q.question_id})
                      </span>
                      <ResultBadge mark={q.user_mark} fullMark={q.full_mark} />
                    </div>

                    {q.text && (
                      <p className="text-sm">{q.text}</p>
                    )}

                    {q.question_image && (
                      <img
                        src={api.imageUrl.question(q.question_id)}
                        alt="вопрос"
                        className="w-full max-h-64 object-contain rounded-lg border"
                        onError={(e) => (e.currentTarget.style.display = "none")}
                      />
                    )}

                    <div className="space-y-1.5 text-sm border-t pt-3">
                      <div className="flex gap-2">
                        <span className="text-[var(--color-muted-foreground)] shrink-0">
                          {stats.detailed ? "Ответ ученика:" : "Твой ответ:"}
                        </span>
                        <span className={getResultColor(q.user_mark, q.full_mark)}>
                          {q.user_answer || "—"}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-[var(--color-muted-foreground)] shrink-0">Верный ответ:</span>
                        <span className="text-green-600 dark:text-green-400 font-medium">{q.answer}</span>
                      </div>
                      {q.answer_image && (
                        <img
                          src={api.imageUrl.answer(q.question_id)}
                          alt="ответ"
                          className="w-full max-h-48 object-contain rounded-lg border mt-2"
                          onError={(e) => (e.currentTarget.style.display = "none")}
                        />
                      )}
                      <div className="flex gap-2 text-xs text-[var(--color-muted-foreground)]">
                        <span>Баллы:</span>
                        <span className={`font-medium ${getResultColor(q.user_mark, q.full_mark)}`}>
                          {q.user_mark} из {q.full_mark}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
