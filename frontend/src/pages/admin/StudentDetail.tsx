import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Trash2, ExternalLink, BookOpen, FlaskConical } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

type WorkStat = {
  work_id: number;
  name: string;
  type: string;
  start: string | null;
  end: string | null;
  final_mark: number;
  max_mark: number;
  fully: number;
  semi: number;
  zero: number;
  questions_amount: number;
};

type UserInfo = { id: number; telegram_id: number; name: string };

type WorkDetail = {
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
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
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

function getWorkTypeBadge(type: string) {
  if (type === "ege") return <Badge variant="default">ЕГЭ</Badge>;
  if (type === "topic") return <Badge variant="secondary">Тема</Badge>;
  return <Badge variant="outline">Тренировка</Badge>;
}

function ScoreBar({ fully, semi, zero, total }: { fully: number; semi: number; zero: number; total: number }) {
  if (total === 0) return null;
  return (
    <div className="flex rounded-full overflow-hidden h-2 mt-2">
      <div className="bg-green-500 transition-all" style={{ width: `${(fully / total) * 100}%` }} />
      <div className="bg-yellow-500 transition-all" style={{ width: `${(semi / total) * 100}%` }} />
      <div className="bg-red-500 transition-all" style={{ width: `${(zero / total) * 100}%` }} />
    </div>
  );
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

function WorkDetailPanel({ detail, loading }: { detail: WorkDetail | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20 text-[var(--color-muted-foreground)]">
        <FlaskConical className="h-10 w-10 mb-3 opacity-30 animate-pulse" />
        <p className="text-sm">Загрузка...</p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20 text-[var(--color-muted-foreground)]">
        <BookOpen className="h-12 w-12 mb-3 opacity-20" />
        <p className="text-sm">Выберите работу для просмотра статистики</p>
      </div>
    );
  }

  const total = detail.general.fully + detail.general.semi + detail.general.zero;

  return (
    <div className="space-y-4">
      {/* General */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{detail.general.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="space-y-1">
              <p className="text-lg font-bold text-[var(--color-primary)]">
                {detail.general.final_mark} из {detail.general.max_mark} б.
              </p>
            </div>
            <div className="space-y-1">
              <div className="flex justify-center gap-2 text-lg font-semibold">
                <span className="flex items-center gap-1 text-green-600">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500 shrink-0" />
                  {detail.general.fully}
                </span>
                <span className="flex items-center gap-1 text-yellow-500">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500 shrink-0" />
                  {detail.general.semi}
                </span>
                <span className="flex items-center gap-1 text-red-500">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500 shrink-0" />
                  {detail.general.zero}
                </span>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">
                {formatDuration(detail.general.start, detail.general.end)}
              </p>
              <p className="text-xs text-[var(--color-muted-foreground)]">затрачено</p>
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex rounded-full overflow-hidden h-3">
              {detail.general.fully > 0 && (
                <div className="bg-green-500" style={{ width: `${(detail.general.fully / total) * 100}%` }} />
              )}
              {detail.general.semi > 0 && (
                <div className="bg-yellow-500" style={{ width: `${(detail.general.semi / total) * 100}%` }} />
              )}
              {detail.general.zero > 0 && (
                <div className="bg-red-500" style={{ width: `${(detail.general.zero / total) * 100}%` }} />
              )}
            </div>
            <p className="text-xs text-[var(--color-muted-foreground)] text-right">
              Завершено: {formatDate(detail.general.end)}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Questions */}
      <h2 className="font-semibold flex items-center gap-2 text-sm">
        <BookOpen className="h-4 w-4" />
        Подробности
      </h2>

      {detail.questions.map((q) => (
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

            {q.text && <p className="text-sm whitespace-pre-wrap">{q.text}</p>}

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
                <span className="text-[var(--color-muted-foreground)] shrink-0">Ответ ученика:</span>
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
  );
}

export function StudentDetail() {
  const { telegramId } = useParams<{ telegramId: string }>();
  const navigate = useNavigate();

  const [works, setWorks] = useState<WorkStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [selectedWorkId, setSelectedWorkId] = useState<number | null>(null);
  const [workDetail, setWorkDetail] = useState<WorkDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!telegramId) return;
    const tid = Number(telegramId);

    Promise.all([
      api.getUsers().then((users) => users.find((u) => u.telegram_id === tid)),
      api.getUserStats(tid),
    ])
      .then(([userInfo, stats]) => {
        setUser(userInfo ?? null);
        setWorks(stats);
      })
      .catch(() => toast.error("Ошибка загрузки данных"))
      .finally(() => setLoading(false));
  }, [telegramId]);

  const handleSelectWork = (workId: number) => {
    if (!user || !telegramId) return;
    if (selectedWorkId === workId) return;

    setSelectedWorkId(workId);
    setWorkDetail(null);
    setDetailLoading(true);

    api.getStudentWorkStats(String(user.id), telegramId, String(workId), 1)
      .then(setWorkDetail)
      .catch(() => toast.error("Ошибка загрузки статистики работы"))
      .finally(() => setDetailLoading(false));
  };

  const handleDelete = async () => {
    if (!telegramId) return;
    setDeleting(true);
    try {
      await api.deleteUser(Number(telegramId));
      toast.success("Ученик удалён");
      navigate("/admin/students");
    } catch {
      toast.error("Ошибка удаления");
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-[var(--color-muted-foreground)]">Загрузка...</div>;
  }

  const statsUrl = (workId: number) =>
    `/student/view-stats?uuid=${user?.id}&tid=${telegramId}&work=${workId}&detailed=1`;

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:h-full lg:min-h-0">
      {/* Left panel */}
      <div className="lg:w-80 xl:w-96 shrink-0 flex flex-col min-h-0">
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 shrink-0">
          <Button variant="ghost" size="icon" onClick={() => navigate("/admin/students")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold truncate">{user?.name ?? `id${telegramId}`}</h1>
            <p className="text-sm text-[var(--color-muted-foreground)]">id{telegramId}</p>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm" disabled={deleting}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Удалить ученика?</AlertDialogTitle>
                <AlertDialogDescription>
                  Это действие нельзя отменить. Все данные ученика будут удалены.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Отмена</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-[var(--color-destructive)] hover:opacity-90"
                >
                  Удалить
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        {/* Works list */}
        {works.length === 0 ? (
          <div className="text-center py-16 text-[var(--color-muted-foreground)]">
            <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>Завершённых тренировок нет</p>
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto space-y-2">
            {works.map((w) => (
              <Card
                key={w.work_id}
                className={`cursor-pointer transition-colors hover:bg-[var(--color-accent)] ${
                  selectedWorkId === w.work_id
                    ? "bg-[var(--color-accent)]"
                    : ""
                }`}
                onClick={() => handleSelectWork(w.work_id)}
              >
                <CardContent className="pt-3 pb-3">
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm truncate">{w.name}</span>
                        {getWorkTypeBadge(w.type)}
                      </div>
                      <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">
                        {formatDate(w.end)}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5 text-xs">
                        <span className="font-semibold">{w.final_mark} из {w.max_mark} б.</span>
                        <span className="flex items-center gap-0.5 text-green-600">
                          <span className="inline-block h-2 w-2 rounded-full bg-green-500 shrink-0" />
                          {w.fully}
                        </span>
                        <span className="flex items-center gap-0.5 text-yellow-600">
                          <span className="inline-block h-2 w-2 rounded-full bg-yellow-500 shrink-0" />
                          {w.semi}
                        </span>
                        <span className="flex items-center gap-0.5 text-red-500">
                          <span className="inline-block h-2 w-2 rounded-full bg-red-500 shrink-0" />
                          {w.zero}
                        </span>
                      </div>
                      <ScoreBar fully={w.fully} semi={w.semi} zero={w.zero} total={w.questions_amount} />
                    </div>
                    <a
                      href={statsUrl(w.work_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Right panel */}
      <div className="flex-1 min-w-0 overflow-y-auto lg:border-l lg:pl-4">
        <WorkDetailPanel detail={workDetail} loading={detailLoading} />
      </div>
    </div>
  );
}
