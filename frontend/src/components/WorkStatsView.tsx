import { BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

/* ── Shared types ─────────────────────────────────────────────────────── */

export type WorkDetailGeneral = {
  telegram_id: number | null;
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

export type WorkDetailQuestion = {
  index: number;
  question_id: number;
  text: string;
  answer: string;
  user_answer: string;
  user_mark: number;
  full_mark: number;
  question_image: boolean;
  answer_image: boolean;
};

export type WorkDetail = {
  general: WorkDetailGeneral;
  questions: WorkDetailQuestion[];
};

/* ── Utilities ────────────────────────────────────────────────────────── */

export function formatDate(iso: string | null) {
  if (!iso) return "—";
  const utc = iso.endsWith("Z") || iso.includes("+") ? iso : iso.replace(" ", "T") + "Z";
  return new Date(utc).toLocaleString("ru-RU", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function toUtc(iso: string) {
  return iso.endsWith("Z") || iso.includes("+") ? iso : iso.replace(" ", "T") + "Z";
}

export function formatDuration(start: string | null, end: string | null) {
  if (!start || !end) return "—";
  const ms = new Date(toUtc(end)).getTime() - new Date(toUtc(start)).getTime();
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  if (h > 0) return `${h}ч ${m}м ${s}с`;
  if (m > 0) return `${m}м ${s}с`;
  return `${s}с`;
}

export function getResultColor(mark: number, fullMark: number) {
  if (mark === fullMark) return "text-green-600 dark:text-green-400";
  if (mark > 0) return "text-yellow-600 dark:text-yellow-400";
  return "text-red-500 dark:text-red-400";
}

function getBorderColor(mark: number, fullMark: number) {
  if (mark === fullMark) return "#22c55e";
  if (mark > 0) return "#eab308";
  return "#ef4444";
}

export function ResultBadge({ mark, fullMark }: { mark: number; fullMark: number }) {
  if (mark === fullMark) return <Badge variant="success">Верно</Badge>;
  if (mark > 0) return <Badge variant="warning">Частично</Badge>;
  return <Badge variant="destructive">Неверно</Badge>;
}

export function getWorkTypeBadge(type: string) {
  if (type === "ege") return <Badge variant="default">ЕГЭ</Badge>;
  if (type === "topic") return <Badge variant="secondary">Тема</Badge>;
  return <Badge variant="outline">Тренировка</Badge>;
}

/* ── Summary card ─────────────────────────────────────────────────────── */

export function WorkSummaryCard({ general, userName }: {
  general: WorkDetailGeneral;
  userName?: boolean;
}) {
  const total = general.fully + general.semi + general.zero;

  return (
    <div>
      {userName && general.telegram_id && (
        <div className="flex flex-col items-center mb-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={api.imageUrl.user(general.telegram_id)} />
            <AvatarFallback className="text-2xl">
              {general.user_name ? general.user_name.charAt(0).toUpperCase() : "?"}
            </AvatarFallback>
          </Avatar>
          {general.user_name && (
            <p className="mt-2 font-semibold text-base">{general.user_name}</p>
          )}
        </div>
      )}
      <div className="rounded-lg border bg-[var(--color-card)] p-4 space-y-4">
        <div>
          <p className="font-semibold text-base">{general.name}</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="space-y-1">
            <p className="text-lg font-bold text-[var(--color-primary)]">
              {general.final_mark}/{general.max_mark}
            </p>
            <p className="text-xs text-[var(--color-muted-foreground)]">баллы</p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-center gap-2 text-lg font-semibold">
              <span className="flex items-center gap-1 text-green-600">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500 shrink-0" />
                {general.fully}
              </span>
              <span className="flex items-center gap-1 text-yellow-500">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500 shrink-0" />
                {general.semi}
              </span>
              <span className="flex items-center gap-1 text-red-500">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500 shrink-0" />
                {general.zero}
              </span>
            </div>
            <p className="text-xs text-[var(--color-muted-foreground)]">вопросы</p>
          </div>
          <div className="space-y-1">
            <p className="text-lg font-semibold">
              {formatDuration(general.start, general.end)}
            </p>
            <p className="text-xs text-[var(--color-muted-foreground)]">время выполнения</p>
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex rounded-full overflow-hidden h-3">
            {general.fully > 0 && (
              <div className="bg-green-500" style={{ width: `${(general.fully / total) * 100}%` }} />
            )}
            {general.semi > 0 && (
              <div className="bg-yellow-500" style={{ width: `${(general.semi / total) * 100}%` }} />
            )}
            {general.zero > 0 && (
              <div className="bg-red-500" style={{ width: `${(general.zero / total) * 100}%` }} />
            )}
          </div>
          <div className="flex justify-between text-xs text-[var(--color-muted-foreground)]">
            <span>Начало: {formatDate(general.start)}</span>
            <span>Завершено: {formatDate(general.end)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Question card ────────────────────────────────────────────────────── */

type QuestionCardProps = {
  question: WorkDetailQuestion;
  answerLabel?: string;
  onQuestionIdClick?: (id: number) => void;
};

export function QuestionCard({ question: q, answerLabel = "Ответ ученика", onQuestionIdClick }: QuestionCardProps) {
  return (
    <Card
      className="border-l-4"
      style={{ borderLeftColor: getBorderColor(q.user_mark, q.full_mark) }}
    >
      <CardContent className="pt-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-[var(--color-muted-foreground)]">
              Вопрос №{q.index}
            </span>
            {onQuestionIdClick ? (
              <span
                className="inline-flex items-center rounded-md bg-[var(--color-muted)] px-2 py-0.5 text-xs font-medium text-[var(--color-muted-foreground)] cursor-pointer hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)] transition-colors"
                title="Просмотр вопроса"
                onClick={() => onQuestionIdClick(q.question_id)}
              >
                #{q.question_id}
              </span>
            ) : (
              <span className="inline-flex items-center rounded-md bg-[var(--color-muted)] px-2 py-0.5 text-xs font-medium text-[var(--color-muted-foreground)]">
                #{q.question_id}
              </span>
            )}
            <ResultBadge mark={q.user_mark} fullMark={q.full_mark} />
          </div>
        </div>

        {q.text && <p className="text-sm whitespace-pre-wrap">{q.text}</p>}

        {q.question_image && (
          <img
            src={api.imageUrl.question(q.question_id)}
            alt="вопрос"
            className="w-full max-h-64 object-contain rounded-lg border"
            onError={(e) => (e.currentTarget.style.display = "none")}
          />
        )}

        <div className="border-t pt-3">
          <div className="grid grid-cols-3 gap-2 text-sm">
            <span className="text-[var(--color-muted-foreground)]">{answerLabel}</span>
            <span className="text-[var(--color-muted-foreground)]">Верный ответ</span>
            <span className="text-[var(--color-muted-foreground)]">Баллы</span>
            <span className={`font-medium ${getResultColor(q.user_mark, q.full_mark)}`}>{q.user_answer || "—"}</span>
            <span className="text-green-600 dark:text-green-400 font-medium">{q.answer}</span>
            <span className={`font-medium ${getResultColor(q.user_mark, q.full_mark)}`}>{q.user_mark} из {q.full_mark}</span>
          </div>
          {q.answer_image && (
            <img
              src={api.imageUrl.answer(q.question_id)}
              alt="ответ"
              className="w-full max-h-48 object-contain rounded-lg border mt-2"
              onError={(e) => (e.currentTarget.style.display = "none")}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/* ── Questions list section ───────────────────────────────────────────── */

type QuestionsListProps = {
  questions: WorkDetailQuestion[];
  answerLabel?: string;
  onQuestionIdClick?: (id: number) => void;
};

export function QuestionsList({ questions, answerLabel, onQuestionIdClick }: QuestionsListProps) {
  return (
    <>
      <h2 className="font-semibold flex items-center gap-2 text-sm">
        <BookOpen className="h-4 w-4" />
        Подробности
      </h2>
      {questions.map((q) => (
        <QuestionCard
          key={q.question_id}
          question={q}
          answerLabel={answerLabel}
          onQuestionIdClick={onQuestionIdClick}
        />
      ))}
    </>
  );
}
