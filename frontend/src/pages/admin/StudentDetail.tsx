import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Trash2, ExternalLink, BookOpen, FlaskConical } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  type WorkDetail,
  formatDate,
  WorkSummaryCard,
  QuestionsList,
} from "@/components/WorkStatsView";

type WorkStat = {
  work_id: number;
  share_token: string | null;
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

  return (
    <div className="space-y-4">
      <WorkSummaryCard general={detail.general} />
      <QuestionsList questions={detail.questions} answerLabel="Ответ ученика" />
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

  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
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

  const handleSelectWork = (token: string | null) => {
    if (!token) return;
    if (selectedWorkId === token) return;

    setSelectedWorkId(token);
    setWorkDetail(null);
    setDetailLoading(true);

    api.getWorkStats(token)
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

  const statsUrl = (token: string) => `/student/view-stats?token=${token}`;

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
                  selectedWorkId === w.share_token
                    ? "bg-[var(--color-accent)]"
                    : ""
                }`}
                onClick={() => handleSelectWork(w.share_token)}
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
                    {w.share_token && (
                    <a
                      href={statsUrl(w.share_token)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    </a>
                    )}
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
