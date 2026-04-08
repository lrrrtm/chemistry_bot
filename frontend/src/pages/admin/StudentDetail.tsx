import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, BookOpen, ExternalLink, Trash2 } from "lucide-react";

import { api } from "@/lib/api";
import type { User, WorkStat } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  type WorkDetail,
  QuestionsList,
  WorkSummaryCard,
  formatDate,
  getWorkTypeBadge,
} from "@/components/WorkStatsView";

function ScoreBar({ fully, semi, zero, total }: { fully: number; semi: number; zero: number; total: number }) {
  if (total === 0) return null;
  return (
    <div className="mt-2 flex h-2 overflow-hidden rounded-full">
      <div className="bg-green-500 transition-all" style={{ width: `${(fully / total) * 100}%` }} />
      <div className="bg-yellow-500 transition-all" style={{ width: `${(semi / total) * 100}%` }} />
      <div className="bg-red-500 transition-all" style={{ width: `${(zero / total) * 100}%` }} />
    </div>
  );
}

function WorkDetailPanel({ detail, loading }: { detail: WorkDetail | null; loading: boolean }) {
  if (loading) {
    return <div className="py-12 text-center text-[var(--color-muted-foreground)]">Загрузка...</div>;
  }

  if (!detail) {
    return <EmptyState icon={BookOpen} text="Выберите работу для просмотра статистики" className="py-16" />;
  }

  return (
    <div className="space-y-4">
      <WorkSummaryCard general={detail.general} />
      <QuestionsList questions={detail.questions} answerLabel="Ответ ученика" />
    </div>
  );
}

export function StudentDetail() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();

  const [user, setUser] = useState<User | null>(null);
  const [works, setWorks] = useState<WorkStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
  const [workDetail, setWorkDetail] = useState<WorkDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    const numericUserId = Number(userId);

    Promise.all([
      api.getUsers().then((items) => items.find((item) => item.id === numericUserId) ?? null),
      api.getUserStats(numericUserId),
    ])
      .then(([userInfo, stats]) => {
        setUser(userInfo);
        setWorks(stats);
      })
      .catch(() => toast.error("Ошибка загрузки данных"))
      .finally(() => setLoading(false));
  }, [userId]);

  const handleSelectWork = (token: string | null) => {
    if (!token || token === selectedWorkId) return;
    setSelectedWorkId(token);
    setDetailLoading(true);
    setWorkDetail(null);

    api.getWorkStats(token)
      .then(setWorkDetail)
      .catch(() => toast.error("Ошибка загрузки статистики работы"))
      .finally(() => setDetailLoading(false));
  };

  const handleDelete = async () => {
    if (!userId) return;
    setDeleting(true);
    try {
      await api.deleteUser(Number(userId));
      toast.success("Ученик удалён");
      navigate("/admin/students");
    } catch {
      toast.error("Ошибка удаления");
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="py-12 text-center text-[var(--color-muted-foreground)]">Загрузка...</div>;
  }

  const statsUrl = (token: string) => `/student/view-stats?token=${token}`;
  const subtitle = user?.username
    ? `@${user.username}`
    : user?.telegram_id
      ? `Telegram id${user.telegram_id}`
      : `ID ${userId}`;

  return (
    <div className="flex flex-col gap-4 lg:h-full lg:min-h-0 lg:flex-row">
      <div className="flex min-h-0 flex-col lg:w-80 xl:w-96">
        <div className="flex items-center gap-3 pb-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/admin/students")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-bold">{user?.name ?? "Ученик"}</h1>
            <p className="text-sm text-[var(--color-muted-foreground)]">{subtitle}</p>
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
                <AlertDialogAction onClick={handleDelete}>Удалить</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        {works.length === 0 ? (
          <EmptyState icon={BookOpen} text="Завершённых тренировок нет" className="py-16" />
        ) : (
          <div className="flex-1 space-y-2 overflow-y-auto">
            {works.map((work) => (
              <Card
                key={work.work_id}
                className={`cursor-pointer transition-colors hover:bg-[var(--color-accent)] ${
                  selectedWorkId === work.share_token ? "bg-[var(--color-accent)]" : ""
                }`}
                onClick={() => handleSelectWork(work.share_token)}
              >
                <CardContent className="pb-3 pt-3">
                  <div className="flex items-start gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="truncate text-sm font-medium">{work.name}</span>
                        {getWorkTypeBadge(work.type)}
                      </div>
                      <p className="mt-0.5 text-xs text-[var(--color-muted-foreground)]">{formatDate(work.end)}</p>
                      <div className="mt-1.5 flex items-center gap-2 text-xs">
                        <span className="font-semibold">{work.final_mark} из {work.max_mark} б.</span>
                        <span className="flex items-center gap-0.5 text-green-600">{work.fully}</span>
                        <span className="flex items-center gap-0.5 text-yellow-600">{work.semi}</span>
                        <span className="flex items-center gap-0.5 text-red-500">{work.zero}</span>
                      </div>
                      <ScoreBar fully={work.fully} semi={work.semi} zero={work.zero} total={work.questions_amount} />
                    </div>
                    {work.share_token && (
                      <a href={statsUrl(work.share_token)} target="_blank" rel="noopener noreferrer" onClick={(event) => event.stopPropagation()}>
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

      <div className="min-w-0 flex-1 overflow-y-auto lg:border-l lg:pl-4">
        <WorkDetailPanel detail={workDetail} loading={detailLoading} />
      </div>
    </div>
  );
}
