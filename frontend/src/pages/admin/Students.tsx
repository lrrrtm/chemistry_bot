import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Users, BookOpen, FlaskConical, ExternalLink, Trash2, ChevronLeft, Plus, X, Save, Pencil, Check, Copy } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { SearchInput } from "@/components/ui/SearchInput";
import { EmptyState } from "@/components/ui/EmptyState";
import { getInitials, scrollToTop } from "@/lib/utils";
import type { User, QuestionFull, WorkStat } from "@/lib/types";
import {
  type WorkDetail,
  formatDate,
  formatDuration,
  getResultColor,
  ResultBadge,
  getWorkTypeBadge,
} from "@/components/WorkStatsView";

// Module-level cache — survives component unmount/remount within the same session
let _usersCache: User[] | null = null;

function WorkDetailPanel({ detail, loading }: { detail: WorkDetail | null; loading: boolean }) {
  const navigate = useNavigate();
  const [questionDialogOpen, setQuestionDialogOpen] = useState(false);
  const [questionData, setQuestionData] = useState<QuestionFull | null>(null);
  const [questionEdited, setQuestionEdited] = useState<Partial<QuestionFull>>({});
  const [questionLoading, setQuestionLoading] = useState(false);
  const [questionSaving, setQuestionSaving] = useState(false);
  const [newTagInput, setNewTagInput] = useState("");
  const newTagRef = useRef<HTMLInputElement>(null);

  const openQuestionDialog = async (id: number) => {
    setQuestionDialogOpen(true);
    setQuestionData(null);
    setQuestionEdited({});
    setQuestionLoading(true);
    setNewTagInput("");
    try {
      const q = await api.getQuestion(id);
      setQuestionData(q);
      setQuestionEdited({ ...q });
    } catch {
      toast.error("Ошибка загрузки вопроса");
      setQuestionDialogOpen(false);
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleQuestionSave = async () => {
    if (!questionData) return;
    setQuestionSaving(true);
    try {
      await api.updateQuestion(questionData.id, {
        text: questionEdited.text ?? questionData.text,
        answer: questionEdited.answer ?? questionData.answer,
        level: questionEdited.level ?? questionData.level,
        full_mark: questionEdited.full_mark ?? questionData.full_mark,
        tags_list: questionEdited.tags_list ?? questionData.tags_list,
        is_rotate: questionEdited.is_rotate ?? questionData.is_rotate,
        is_selfcheck: questionEdited.is_selfcheck ?? questionData.is_selfcheck,
      });
      toast.success("Вопрос обновлён");
    } catch {
      toast.error("Ошибка сохранения");
    } finally {
      setQuestionSaving(false);
    }
  };

  const addTag = () => {
    const tag = newTagInput.trim();
    if (!tag || !questionData) return;
    const current = questionEdited.tags_list ?? questionData.tags_list;
    if (current.includes(tag)) { toast.warning("Такой тег уже есть"); return; }
    setQuestionEdited((p) => ({ ...p, tags_list: [...current, tag] }));
    setNewTagInput("");
    newTagRef.current?.focus();
  };

  if (loading) {
    return <EmptyState icon={FlaskConical} text="Загрузка..." animate className="h-full py-20" />;
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
          <div className="flex justify-between text-xs text-[var(--color-muted-foreground)]">
            <span>Начало: {formatDate(detail.general.start)}</span>
            <span>Завершено: {formatDate(detail.general.end)}</span>
          </div>
        </div>
      </div>

      <h2 className="font-semibold flex items-center gap-2 text-sm">
        <BookOpen className="h-4 w-4" />
        Подробности
      </h2>

      {detail.questions.map((q) => (
        <Card
          key={q.question_id}
          className="border-l-4"
          style={{
            borderLeftColor:
              q.user_mark === q.full_mark
                ? "#22c55e"
                : q.user_mark > 0
                ? "#eab308"
                : "#ef4444",
          }}
        >
          <CardContent className="pt-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-[var(--color-muted-foreground)]">
                  Вопрос №{q.index}
                </span>
                <span
                  className="inline-flex items-center rounded-md bg-[var(--color-muted)] px-2 py-0.5 text-xs font-medium text-[var(--color-muted-foreground)] cursor-pointer hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)] transition-colors"
                  title="Просмотр вопроса"
                  onClick={() => openQuestionDialog(q.question_id)}
                >
                  #{q.question_id}
                </span>
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
                <span className="text-[var(--color-muted-foreground)]">Ответ ученика</span>
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
      ))}

      <Dialog open={questionDialogOpen} onOpenChange={setQuestionDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          {questionLoading ? (
            <div className="flex items-center justify-center py-12 text-[var(--color-muted-foreground)]">
              <p className="text-sm">Загрузка вопроса...</p>
            </div>
          ) : questionData && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  Вопрос #{questionData.id}
                  <Badge variant="outline" className="text-xs">{questionData.type}</Badge>
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 pt-2">
                <div className="space-y-2">
                  <Label>Текст вопроса</Label>
                  <Textarea
                    value={questionEdited.text ?? questionData.text}
                    onChange={(e) => setQuestionEdited((p) => ({ ...p, text: e.target.value }))}
                    rows={4}
                  />
                </div>

                {questionData.question_image && (
                  <img
                    src={api.imageUrl.question(questionData.id)}
                    alt="вопрос"
                    className="w-full max-h-48 object-contain rounded-lg border"
                    onError={(e) => (e.currentTarget.style.display = "none")}
                  />
                )}

                <div className="space-y-2">
                  <Label>Текст ответа</Label>
                  <Textarea
                    value={questionEdited.answer ?? questionData.answer}
                    onChange={(e) => setQuestionEdited((p) => ({ ...p, answer: e.target.value }))}
                    rows={4}
                  />
                </div>

                {questionData.answer_image && (
                  <img
                    src={api.imageUrl.answer(questionData.id)}
                    alt="ответ"
                    className="w-full max-h-48 object-contain rounded-lg border"
                    onError={(e) => (e.currentTarget.style.display = "none")}
                  />
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>Сложность (1–5)</Label>
                    <Select
                      value={String(questionEdited.level ?? questionData.level)}
                      onValueChange={(v) => setQuestionEdited((p) => ({ ...p, level: Number(v) }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Максимальный балл</Label>
                    <Select
                      value={String(questionEdited.full_mark ?? questionData.full_mark)}
                      onValueChange={(v) => setQuestionEdited((p) => ({ ...p, full_mark: Number(v) }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Теги</Label>
                  <div className="flex gap-2">
                    <Input
                      ref={newTagRef}
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                      placeholder="Новый тег..."
                      className="h-8 text-sm"
                      onKeyDown={(e) => { if (e.key === "Enter") addTag(); }}
                    />
                    <Button size="sm" className="h-8 shrink-0" disabled={!newTagInput.trim()} onClick={addTag}>
                      <Plus className="h-4 w-4 mr-1" />
                      Добавить
                    </Button>
                  </div>
                  {(questionEdited.tags_list ?? questionData.tags_list).length === 0 ? (
                    <p className="text-sm text-[var(--color-muted-foreground)]">Нет тегов</p>
                  ) : (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {(questionEdited.tags_list ?? questionData.tags_list).map((tag) => (
                        <div key={tag} className="flex items-center gap-1.5 bg-[var(--color-accent)] rounded-full px-3 py-1 text-sm">
                          <span>{tag}</span>
                          <button
                            className="ml-0.5 hover:text-[var(--color-destructive)] transition-colors"
                            onClick={() => setQuestionEdited((p) => ({
                              ...p,
                              tags_list: (p.tags_list ?? questionData.tags_list).filter((t) => t !== tag),
                            }))}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-6">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={Boolean(questionEdited.is_rotate ?? questionData.is_rotate)}
                      onCheckedChange={(v) => setQuestionEdited((p) => ({ ...p, is_rotate: Number(v) }))}
                    />
                    <Label>Вращение ответа</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={Boolean(questionEdited.is_selfcheck ?? questionData.is_selfcheck)}
                      onCheckedChange={(v) => setQuestionEdited((p) => ({ ...p, is_selfcheck: Number(v) }))}
                    />
                    <Label>Самопроверка</Label>
                  </div>
                </div>

                <div className="flex justify-between pt-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setQuestionDialogOpen(false);
                      navigate("/admin/pool", { state: { openQuestionId: questionData.id } });
                    }}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Открыть в пуле
                  </Button>
                  <Button onClick={handleQuestionSave} disabled={questionSaving}>
                    <Save className="h-4 w-4 mr-2" />
                    {questionSaving ? "Сохранение..." : "Сохранить"}
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function Students() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [creatingUser, setCreatingUser] = useState(false);
  const [inviteDialog, setInviteDialog] = useState<{ name: string; inviteUrl: string; expiresAt: string } | null>(null);

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [works, setWorks] = useState<WorkStat[]>([]);
  const [worksLoading, setWorksLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState("");
  const [savingName, setSavingName] = useState(false);

  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
  const [workDetail, setWorkDetail] = useState<WorkDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Mobile step: 0 = student list, 1 = works list, 2 = work detail
  const [mobileStep, setMobileStep] = useState<0 | 1 | 2>(0);

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
    if (selectedUser?.id === user.id) return;
    setSelectedUser(user);
    setWorks([]);
    setSelectedWorkId(null);
    setWorkDetail(null);
    setWorksLoading(true);
    setMobileStep(1);
    scrollToTop();
    api.getUserStats(user.id)
      .then(setWorks)
      .catch(() => toast.error("Ошибка загрузки работ"))
      .finally(() => setWorksLoading(false));
  };

  const handleSelectWork = (token: string | null) => {
    if (!selectedUser || selectedWorkId === token || !token) return;
    setSelectedWorkId(token);
    setWorkDetail(null);
    setDetailLoading(true);
    setMobileStep(2);
    scrollToTop();
    api.getWorkStats(token)
      .then(setWorkDetail)
      .catch(() => toast.error("Ошибка загрузки статистики"))
      .finally(() => setDetailLoading(false));
  };

  const handleDelete = async () => {
    if (!selectedUser) return;
    setDeleting(true);
    try {
      await api.deleteUser(selectedUser.id);
      const updated = users.filter((u) => u.id !== selectedUser.id);
      _usersCache = updated;
      setUsers(updated);
      setSelectedUser(null);
      setWorks([]);
      setSelectedWorkId(null);
      setWorkDetail(null);
      setMobileStep(0);
      scrollToTop();
      toast.success("Ученик удалён");
    } catch {
      toast.error("Ошибка удаления");
    } finally {
      setDeleting(false);
    }
  };

  const handleStartEdit = () => {
    if (!selectedUser) return;
    setEditNameValue(selectedUser.name);
    setEditingName(true);
  };

  const handleSaveName = async () => {
    if (!selectedUser || !editNameValue.trim()) return;
    setSavingName(true);
    try {
      await api.renameUser(selectedUser.id, editNameValue.trim());
      const newName = editNameValue.trim();
      setSelectedUser({ ...selectedUser, name: newName });
      const updated = users.map((u) =>
        u.id === selectedUser.id ? { ...u, name: newName } : u
      );
      _usersCache = updated;
      setUsers(updated);
      setEditingName(false);
      toast.success("Имя изменено");
    } catch {
      toast.error("Ошибка сохранения");
    } finally {
      setSavingName(false);
    }
  };

  const buildInviteUrl = (inviteUrl: string | null, inviteToken: string) => {
    if (inviteUrl) return inviteUrl;
    return `${window.location.origin}/tma/?invite=${encodeURIComponent(inviteToken)}`;
  };

  const handleCreateStudent = async () => {
    const name = createName.trim();
    if (!name) return;
    setCreatingUser(true);
    try {
      const result = await api.createStudent(name);
      const nextUsers = [...users, result.user].sort((left, right) => left.name.localeCompare(right.name, "ru"));
      _usersCache = nextUsers;
      setUsers(nextUsers);
      setCreateDialogOpen(false);
      setCreateName("");
      setInviteDialog({
        name: result.user.name,
        inviteUrl: buildInviteUrl(result.invite_url, result.invite_token),
        expiresAt: result.invite_expires_at,
      });
      toast.success("Профиль ученика создан");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Ошибка создания ученика");
    } finally {
      setCreatingUser(false);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      (u.username ?? "").toLowerCase().includes(search.toLowerCase()) ||
      String(u.telegram_id ?? "").includes(search)
  );

  const statsUrl = (token: string) =>
    `/student/view-stats?token=${token}`;

  if (loading) {
    return (
      <div className="text-center text-[var(--color-muted-foreground)] py-12">Загрузка...</div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row lg:h-full lg:min-h-0 border rounded-lg overflow-hidden">
      {/* ── Column 1: Student list ─────────────────────────────────────────── */}
      <div className={`${mobileStep !== 0 ? "hidden lg:flex" : "flex"} flex-col lg:w-80 shrink-0 min-h-0 border-b lg:border-b-0 lg:border-r`}>
        <div className="px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)] min-h-[48px] flex items-center gap-2">
          <SearchInput
            placeholder="Поиск..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-7 text-xs"
            wrapperClassName="flex-1"
          />
          <Button size="sm" className="h-7 shrink-0 px-2" onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-3.5 w-3.5 mr-1" />
            Новый
          </Button>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto">
          {filtered.length === 0 ? (
            <EmptyState icon={Users} text={search ? "Не найдено" : "Нет учеников"} />
          ) : (
            filtered.map((user) => (
              <div
                key={user.id}
                className={`group flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-[var(--color-accent)] transition-colors ${
                  selectedUser?.id === user.id
                    ? "bg-[var(--color-accent)] font-medium"
                    : ""
                }`}
                onClick={() => handleSelectUser(user)}
              >
                <Avatar className="h-7 w-7 shrink-0">
                  {user.telegram_id ? <AvatarImage src={api.imageUrl.user(user.telegram_id)} alt={user.name} /> : null}
                  <AvatarFallback className="text-[10px] font-semibold">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{user.name}</p>
                  <p className="text-[10px] text-[var(--color-muted-foreground)]">
                    {user.username ? `@${user.username}` : user.telegram_id ? `Telegram id${user.telegram_id}` : "Веб-профиль"}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 2: Works list ───────────────────────────────────────────── */}
      <div className={`${mobileStep !== 1 ? "hidden lg:flex" : "flex"} flex-col lg:w-72 shrink-0 min-h-0 border-b lg:border-b-0 lg:border-r`}>
        <div className="flex items-center justify-between px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)] min-h-[48px]">
          <div className="flex items-center gap-1.5 min-w-0 flex-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 lg:hidden"
              onClick={() => { setMobileStep(0); setEditingName(false); scrollToTop(); }}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {editingName && selectedUser ? (
              <div className="flex items-center gap-1 flex-1 min-w-0">
                <Input
                  value={editNameValue}
                  onChange={(e) => setEditNameValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSaveName(); if (e.key === "Escape") setEditingName(false); }}
                  className="h-6 text-xs flex-1 min-w-0"
                  autoFocus
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 text-green-600 hover:text-green-700"
                  onClick={handleSaveName}
                  disabled={savingName || !editNameValue.trim()}
                >
                  <Check className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0"
                  onClick={() => setEditingName(false)}
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
            ) : (
              <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)] truncate">
                {selectedUser ? selectedUser.name : "Работы"}
              </span>
            )}
          </div>
          {selectedUser && !editingName && (
            <div className="flex items-center gap-0.5 shrink-0">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleStartEdit}
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-[var(--color-destructive)] hover:text-[var(--color-destructive)]"
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
            </div>
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
            <EmptyState icon={BookOpen} text="Нет завершённых тренировок" />
          ) : (
            works.map((w) => (
              <div
                key={w.work_id}
                className={`group flex items-start gap-2 px-3 py-2.5 cursor-pointer hover:bg-[var(--color-accent)] transition-colors border-b last:border-b-0 ${
                  selectedWorkId === w.share_token ? "bg-[var(--color-accent)]" : ""
                }`}
                onClick={() => handleSelectWork(w.share_token)}
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
                    <span className="font-semibold">{w.final_mark}/{w.max_mark} б.</span>
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
                </div>
                {w.share_token && (
                <a
                  href={statsUrl(w.share_token)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 opacity-0 group-hover:opacity-70 hover:!opacity-100 transition-opacity mt-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 3: Work detail ──────────────────────────────────────────── */}
      <div className={`${mobileStep !== 2 ? "hidden lg:flex" : "flex"} flex-col flex-1 min-w-0 min-h-0`}>
        {/* Mobile nav bar */}
        <div className="flex items-center gap-2 px-3 py-2 border-b shrink-0 bg-[var(--color-card)] lg:hidden">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1 h-7 px-2 text-xs"
            onClick={() => { setMobileStep(1); scrollToTop(); }}
          >
            <ChevronLeft className="h-4 w-4" />
            Работы
          </Button>
          {selectedUser && selectedWorkId && (
            <a
              href={statsUrl(selectedWorkId)}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto"
            >
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </a>
          )}
        </div>
        <div className="flex-1 min-h-0 overflow-y-auto p-4">
          <WorkDetailPanel detail={workDetail} loading={detailLoading} />
        </div>
      </div>

      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Новый ученик</DialogTitle>
            <DialogDescription>
              Создадим профиль и сразу выдадим инвайт-ссылку для первого входа.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="student-name">Имя ученика</Label>
              <Input
                id="student-name"
                value={createName}
                onChange={(event) => setCreateName(event.target.value)}
                placeholder="Например, Анна Петрова"
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    void handleCreateStudent();
                  }
                }}
              />
            </div>
            <Button className="w-full" disabled={creatingUser || !createName.trim()} onClick={() => void handleCreateStudent()}>
              {creatingUser ? "Создание..." : "Создать и получить инвайт"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(inviteDialog)} onOpenChange={(open) => !open && setInviteDialog(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Инвайт готов</DialogTitle>
            <DialogDescription>{inviteDialog?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Ссылка для ученика</Label>
              <div className="flex gap-2">
                <Input readOnly value={inviteDialog?.inviteUrl ?? ""} onClick={(event) => (event.target as HTMLInputElement).select()} />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    if (!inviteDialog) return;
                    navigator.clipboard.writeText(inviteDialog.inviteUrl);
                    toast.success("Инвайт скопирован");
                  }}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <p className="text-sm text-[var(--color-muted-foreground)]">
              После открытия ссылки ученик придумает логин и пароль и дальше будет входить по ним.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
