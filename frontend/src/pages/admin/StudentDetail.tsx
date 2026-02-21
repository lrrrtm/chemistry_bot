import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Trash2, ExternalLink, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
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

export function StudentDetail() {
  const { telegramId } = useParams<{ telegramId: string }>();
  const navigate = useNavigate();
  const [works, setWorks] = useState<WorkStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [deleting, setDeleting] = useState(false);

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

  if (loading) return <div className="text-center py-12 text-[var(--color-muted-foreground)]">Загрузка...</div>;

  const statsUrl = (workId: number) =>
    `/student/view-stats?uuid=${user?.id}&tid=${telegramId}&work=${workId}&detailed=1`;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
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
              <Trash2 className="h-4 w-4 mr-1" />
              Удалить
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
              <AlertDialogAction onClick={handleDelete} className="bg-[var(--color-destructive)] hover:opacity-90">
                Удалить
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {works.length === 0 ? (
        <div className="text-center py-16 text-[var(--color-muted-foreground)]">
          <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>Завершённых тренировок нет</p>
        </div>
      ) : (
        <div className="space-y-3">
          {works.map((w) => (
            <Card key={w.work_id}>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm truncate">{w.name}</span>
                      {getWorkTypeBadge(w.type)}
                    </div>
                    <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">
                      {formatDate(w.end)}
                    </p>
                    <div className="flex gap-3 mt-2 text-sm">
                      <span className="text-[var(--color-foreground)] font-semibold">
                        {w.final_mark} / {w.max_mark}
                      </span>
                      <span className="text-green-600">{w.fully} ✓</span>
                      <span className="text-yellow-600">{w.semi} ~</span>
                      <span className="text-red-500">{w.zero} ✗</span>
                    </div>
                    <ScoreBar fully={w.fully} semi={w.semi} zero={w.zero} total={w.questions_amount} />
                  </div>
                  <a
                    href={statsUrl(w.work_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0"
                  >
                    <Button variant="ghost" size="icon">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
