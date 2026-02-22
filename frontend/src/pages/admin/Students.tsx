import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Search, Users, BookOpen, FlaskConical, ExternalLink, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

type User = { id: number; telegram_id: number; name: string };

// Module-level cache — survives component unmount/remount within the same session
let _usersCache: User[] | null = null;

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

function getInitials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

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
  const navigate = useNavigate();

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
      <div className="rounded-lg border bg-[var(--color-card)] p-4 space-y-4">
        <p className="font-semibold text-base">{detail.general.name}</p>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="space-y-1">
            <p className="text-lg font-bold text-[var(--color-primary)]">
              {detail.general.final_mark} / {detail.general.max_mark}
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
      </div>

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
              <div className="flex items-center gap-1.5">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
                  title="Открыть в пуле вопросов"
                  onClick={() => navigate("/admin/pool", { state: { openQuestionId: q.question_id } })}
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </Button>
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

export function Students() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [works, setWorks] = useState<WorkStat[]>([]);
  const [worksLoading, setWorksLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [selectedWorkId, setSelectedWorkId] = useState<number | null>(null);
  const [workDetail, setWorkDetail] = useState<WorkDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (_usersCache) {
      setUsers(_usersCache);
      setLoading(false);
      return;
    }
    api.getUsers()
      .then((data) => { _usersCache = data; setUsers(data); })
      .catch(() => toast.error("Ошибка загрузки учеников"))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectUser = (user: User) => {
    if (selectedUser?.telegram_id === user.telegram_id) return;
    setSelectedUser(user);
    setWorks([]);
    setSelectedWorkId(null);
    setWorkDetail(null);
    setWorksLoading(true);
    api.getUserStats(user.telegram_id)
      .then(setWorks)
      .catch(() => toast.error("Ошибка загрузки работ"))
      .finally(() => setWorksLoading(false));
  };

  const handleSelectWork = (workId: number) => {
    if (!selectedUser || selectedWorkId === workId) return;
    setSelectedWorkId(workId);
    setWorkDetail(null);
    setDetailLoading(true);
    api.getStudentWorkStats(
      String(selectedUser.id),
      String(selectedUser.telegram_id),
      String(workId),
      1
    )
      .then(setWorkDetail)
      .catch(() => toast.error("Ошибка загрузки статистики"))
      .finally(() => setDetailLoading(false));
  };

  const handleDelete = async () => {
    if (!selectedUser) return;
    setDeleting(true);
    try {
      await api.deleteUser(selectedUser.telegram_id);
      const updated = users.filter((u) => u.telegram_id !== selectedUser.telegram_id);
      _usersCache = updated;
      setUsers(updated);
      setSelectedUser(null);
      setWorks([]);
      setSelectedWorkId(null);
      setWorkDetail(null);
      toast.success("Ученик удалён");
    } catch {
      toast.error("Ошибка удаления");
    } finally {
      setDeleting(false);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      String(u.telegram_id).includes(search)
  );

  const statsUrl = (workId: number) =>
    `/student/view-stats?uuid=${selectedUser?.id}&tid=${selectedUser?.telegram_id}&work=${workId}&detailed=1`;

  if (loading) {
    return (
      <div className="text-center text-[var(--color-muted-foreground)] py-12">Загрузка...</div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row lg:h-full lg:min-h-0 border rounded-lg overflow-hidden">
      {/* ── Column 1: Student list ─────────────────────────────────────────── */}
      <div className="lg:w-80 shrink-0 flex flex-col min-h-0 border-b lg:border-b-0 lg:border-r">
        <div className="px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)]">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--color-muted-foreground)]" />
            <Input
              placeholder="Поиск..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-7 pl-8 text-xs"
            />
          </div>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-[var(--color-muted-foreground)]">
              <Users className="h-8 w-8 mb-2 opacity-30" />
              <p className="text-xs">{search ? "Не найдено" : "Нет учеников"}</p>
            </div>
          ) : (
            filtered.map((user) => (
              <div
                key={user.telegram_id}
                className={`group flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-[var(--color-accent)] transition-colors ${
                  selectedUser?.telegram_id === user.telegram_id
                    ? "bg-[var(--color-accent)] font-medium"
                    : ""
                }`}
                onClick={() => handleSelectUser(user)}
              >
                <Avatar className="h-7 w-7 shrink-0">
                  <AvatarImage src={api.imageUrl.user(user.telegram_id)} alt={user.name} />
                  <AvatarFallback className="text-[10px] font-semibold">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{user.name}</p>
                  <p className="text-[10px] text-[var(--color-muted-foreground)]">
                    id{user.telegram_id}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 2: Works list ───────────────────────────────────────────── */}
      <div className="lg:w-72 shrink-0 flex flex-col min-h-0 border-b lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)] min-h-[48px]">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)] truncate">
            {selectedUser ? selectedUser.name : "Работы"}
          </span>
          {selectedUser && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 text-[var(--color-destructive)] hover:text-[var(--color-destructive)]"
                  disabled={deleting}
                >
                  <Trash2 className="h-3.5 w-3.5" />
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
          )}
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto">
          {!selectedUser ? (
            <p className="text-center py-6 text-xs text-[var(--color-muted-foreground)]">
              Выберите ученика
            </p>
          ) : worksLoading ? (
            <p className="text-center py-6 text-xs text-[var(--color-muted-foreground)]">
              Загрузка...
            </p>
          ) : works.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-[var(--color-muted-foreground)]">
              <BookOpen className="h-8 w-8 mb-2 opacity-30" />
              <p className="text-xs">Нет завершённых тренировок</p>
            </div>
          ) : (
            works.map((w) => (
              <div
                key={w.work_id}
                className={`group flex items-start gap-2 px-3 py-2.5 cursor-pointer hover:bg-[var(--color-accent)] transition-colors border-b last:border-b-0 ${
                  selectedWorkId === w.work_id ? "bg-[var(--color-accent)]" : ""
                }`}
                onClick={() => handleSelectWork(w.work_id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-sm font-medium truncate">{w.name}</span>
                    {getWorkTypeBadge(w.type)}
                  </div>
                  <p className="text-xs text-[var(--color-muted-foreground)] mt-0.5">
                    {formatDate(w.end)}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-xs">
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
                  className="shrink-0 opacity-0 group-hover:opacity-70 hover:!opacity-100 transition-opacity mt-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 3: Work detail ──────────────────────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col min-h-0">
        <div className="flex-1 min-h-0 overflow-y-auto p-4">
          <WorkDetailPanel detail={workDetail} loading={detailLoading} />
        </div>
      </div>
    </div>
  );
}
