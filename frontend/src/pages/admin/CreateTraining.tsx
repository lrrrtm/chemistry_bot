import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Send, Filter, ChevronDown, ChevronRight, Plus, X, Copy, Check, Search } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";

type User = { id: number; telegram_id: number; name: string };

type TopicTag = { tag: string; count: number };
type TopicItem = { id: number; name: string; tags: TopicTag[] };
type TopicsData = Record<string, TopicItem[]>;

interface QuestionCounts {
  [tag: string]: number;
}

export function CreateTraining() {
  const [topics, setTopics] = useState<TopicsData>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Tags mode state
  const [workName, setWorkName] = useState(() => `Тренировка по темам (${new Date().toLocaleString("ru-RU")})`);
  const [questionCounts, setQuestionCounts] = useState<QuestionCounts>({});
  const [expandedVolumes, setExpandedVolumes] = useState<Set<string>>(new Set());

  // Hard filter mode state
  const [hardName, setHardName] = useState(() => `Тренировка по тегам (${new Date().toLocaleString("ru-RU")})`);
  const [hardTags, setHardTags] = useState<string[]>(["", ""]);
  const [hardCount, setHardCount] = useState(10);
  const [activeTagField, setActiveTagField] = useState<number | null>(null);

  // Success dialog state
  const [successDialog, setSuccessDialog] = useState<{ name: string; link: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [sending, setSending] = useState<number | null>(null);
  const userSearchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getTopics()
      .then((data) => {
        setTopics(data);
      })
      .catch(() => toast.error("Ошибка загрузки тем"))
      .finally(() => setLoading(false));
    api.getUsers().then(setUsers).catch(() => {});
  }, []);

  // All unique tags from all topics (for autocomplete)
  const allTags = useMemo(() => {
    const set = new Set<string>();
    Object.values(topics).forEach((topicList) =>
      topicList.forEach((topic) =>
        topic.tags.forEach(({ tag }) => set.add(tag))
      )
    );
    return Array.from(set).sort();
  }, [topics]);

  const getSuggestions = (value: string, index: number) => {
    if (!value.trim()) return [];
    const lower = value.toLowerCase();
    const used = new Set(hardTags.filter((t, i) => i !== index && t));
    return allTags
      .filter((t) => t.toLowerCase().includes(lower) && !used.has(t))
      .slice(0, 8);
  };

  const updateCount = (tag: string, value: number) => {
    setQuestionCounts((prev) => {
      const next = { ...prev };
      if (value <= 0) delete next[tag];
      else next[tag] = value;
      return next;
    });
  };

  const totalSelected = Object.values(questionCounts).reduce((a, b) => a + b, 0);

  const handleCreateByTags = async () => {
    if (totalSelected === 0) {
      toast.warning("Добавьте хотя бы один вопрос");
      return;
    }
    setSubmitting(true);
    try {
      const result = await api.createHandWork({
        name: workName || `Тренировка по темам (${new Date().toLocaleString("ru-RU")})`,
        questions: questionCounts,
        mode: "tags",
      });
      setQuestionCounts({});
      if (result.link) {
        setSuccessDialog({ name: result.name, link: result.link });
      } else {
        toast.success("Тренировка создана!");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка создания тренировки");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateHardFilter = async () => {
    const tags = hardTags.filter(Boolean);
    if (tags.length < 2) {
      toast.warning("Введите минимум 2 тега");
      return;
    }
    setSubmitting(true);
    try {
      const result = await api.createHandWork({
        name: hardName,
        questions: {},
        mode: "hard_filter",
        hard_tags: tags,
        questions_count: hardCount,
      });
      if (result.link) {
        setSuccessDialog({ name: result.name, link: result.link });
      } else {
        toast.success("Тренировка создана!");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка создания тренировки");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyLink = () => {
    if (!successDialog) return;
    navigator.clipboard.writeText(successDialog.link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleSendToUser = async (user: User) => {
    if (!successDialog || sending) return;
    setSending(user.telegram_id);
    try {
      await api.sendTrainingToUser({
        telegram_id: user.telegram_id,
        link: successDialog.link,
        name: successDialog.name,
      });
      toast.success(`Отправлено ${user.name}`);
    } catch {
      toast.error(`Ошибка отправки ${user.name}`);
    } finally {
      setSending(null);
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(userSearch.toLowerCase()) ||
      String(u.telegram_id).includes(userSearch)
  );

  const toggleVolume = (volume: string) => {
    setExpandedVolumes((prev) => {
      const next = new Set(prev);
      if (next.has(volume)) next.delete(volume);
      else next.add(volume);
      return next;
    });
  };

  if (loading) {
    return <div className="text-center text-[var(--color-muted-foreground)] py-12">Загрузка...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Создание тренировки</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
          Выберите темы и количество вопросов для персональной тренировки
        </p>
      </div>

      <Tabs defaultValue="tags">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="tags" className="flex-1 sm:flex-none">По темам</TabsTrigger>
          <TabsTrigger value="hard" className="flex-1 sm:flex-none">По тегам</TabsTrigger>
        </TabsList>

        {/* BY TAGS */}
        <TabsContent value="tags" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-2">
                <Label htmlFor="work-name">Название тренировки</Label>
                <Input
                  id="work-name"
                  value={workName}
                  onChange={(e) => setWorkName(e.target.value)}
                  placeholder="Введите название"
                />
              </div>
            </CardContent>
          </Card>

          {Object.entries(topics).map(([volume, topicList]) => (
            <Card key={volume}>
              <button
                className="w-full text-left"
                onClick={() => toggleVolume(volume)}
              >
                <CardHeader className={expandedVolumes.has(volume) ? "pb-3" : ""}>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{volume}</CardTitle>
                    {expandedVolumes.has(volume) ? (
                      <ChevronDown className="h-4 w-4 text-[var(--color-muted-foreground)]" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-[var(--color-muted-foreground)]" />
                    )}
                  </div>
                </CardHeader>
              </button>

              {expandedVolumes.has(volume) && (
                <CardContent className="pt-0 space-y-4">
                  {topicList.map((topic) => (
                    <div key={topic.id}>
                      <p className="font-medium text-sm mb-2">{topic.name}</p>
                      <div className="space-y-1.5">
                        {topic.tags.map(({ tag, count }) => (
                          <div
                            key={tag}
                            className="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-[var(--color-muted)] transition-colors"
                          >
                            <span className="flex-1 text-sm truncate">{tag}</span>
                            <span className="text-xs text-[var(--color-muted-foreground)] shrink-0">
                              ({count} шт)
                            </span>
                            <div className="flex items-center gap-1">
                              <Input
                                type="number"
                                min={0}
                                max={count}
                                value={questionCounts[tag] ?? 0}
                                onChange={(e) =>
                                  updateCount(tag, Math.min(Math.max(0, Number(e.target.value)), count))
                                }
                                className="w-16 h-7 text-center text-sm px-1"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </CardContent>
              )}
            </Card>
          ))}

          <div className="sticky bottom-4 flex items-center justify-between bg-[var(--color-card)] border rounded-lg px-4 py-3 shadow-lg">
            <span className="text-sm">
              Выбрано: <strong>{totalSelected}</strong> вопр.
            </span>
            <Button onClick={handleCreateByTags} disabled={submitting || totalSelected === 0}>
              <Send className="h-4 w-4 mr-2" />
              {submitting ? "Создание..." : "Создать"}
            </Button>
          </div>
        </TabsContent>

        {/* HARD FILTER */}
        <TabsContent value="hard" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Жёсткий фильтр по тегам
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hard-name">Название тренировки</Label>
                <Input
                  id="hard-name"
                  value={hardName}
                  onChange={(e) => setHardName(e.target.value)}
                  placeholder="Введите название"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="hard-count">Количество вопросов</Label>
                <Input
                  id="hard-count"
                  type="number"
                  min={1}
                  value={hardCount}
                  onChange={(e) => setHardCount(Number(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label>Теги (минимум 2) — вопрос должен содержать ВСЕ указанные теги</Label>
                {hardTags.map((tag, i) => {
                  const suggestions = activeTagField === i ? getSuggestions(tag, i) : [];
                  return (
                    <div key={i} className="relative flex gap-2">
                      <div className="relative flex-1">
                        <Input
                          value={tag}
                          placeholder={`Тег №${i + 1}`}
                          onFocus={() => setActiveTagField(i)}
                          onBlur={() => setActiveTagField(null)}
                          onChange={(e) => {
                            const next = [...hardTags];
                            next[i] = e.target.value;
                            setHardTags(next);
                          }}
                        />
                        {suggestions.length > 0 && (
                          <ul className="absolute z-50 left-0 right-0 top-full mt-1 bg-[var(--color-card)] border rounded-md shadow-md max-h-48 overflow-y-auto">
                            {suggestions.map((s) => (
                              <li
                                key={s}
                                className="px-3 py-1.5 text-sm cursor-pointer hover:bg-[var(--color-accent)] select-none"
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  const next = [...hardTags];
                                  next[i] = s;
                                  setHardTags(next);
                                  setActiveTagField(null);
                                }}
                              >
                                {s}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-9 w-9 shrink-0"
                        disabled={hardTags.length <= 2}
                        onClick={() => setHardTags(hardTags.filter((_, j) => j !== i))}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  );
                })}
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-1"
                  onClick={() => setHardTags([...hardTags, ""])}
                >
                  <Plus className="h-4 w-4 mr-1.5" />
                  Добавить тег
                </Button>
              </div>

              <Button className="w-full" onClick={handleCreateHardFilter} disabled={submitting}>
                <Send className="h-4 w-4 mr-2" />
                {submitting ? "Создание..." : "Создать тренировку"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Success dialog */}
      <Dialog
        open={!!successDialog}
        onOpenChange={(open) => {
          if (!open) {
            setSuccessDialog(null);
            setCopied(false);
            setUserSearch("");
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Тренировка создана</DialogTitle>
            <DialogDescription>
              {successDialog?.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Copy link */}
            <div className="space-y-1.5">
              <Label className="text-xs text-[var(--color-muted-foreground)]">Ссылка</Label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={successDialog?.link ?? ""}
                  className="text-sm"
                  onClick={(e) => (e.target as HTMLInputElement).select()}
                />
                <Button variant="outline" size="icon" className="shrink-0" onClick={handleCopyLink}>
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* Send to student */}
            <div className="space-y-1.5">
              <Label className="text-xs text-[var(--color-muted-foreground)]">Отправить ученику</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--color-muted-foreground)]" />
                <Input
                  ref={userSearchRef}
                  placeholder="Поиск по имени..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="pl-8 text-sm"
                />
              </div>
              <div className="max-h-48 overflow-y-auto rounded-md border">
                {filteredUsers.length === 0 ? (
                  <p className="text-center py-4 text-xs text-[var(--color-muted-foreground)]">
                    {userSearch ? "Не найдено" : "Нет учеников"}
                  </p>
                ) : (
                  filteredUsers.map((user) => (
                    <div
                      key={user.telegram_id}
                      className="flex items-center justify-between px-3 py-2 hover:bg-[var(--color-accent)] transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="text-sm truncate">{user.name}</p>
                        <p className="text-[10px] text-[var(--color-muted-foreground)]">id{user.telegram_id}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="shrink-0 h-7 px-2"
                        disabled={sending === user.telegram_id}
                        onClick={() => handleSendToUser(user)}
                      >
                        <Send className="h-3.5 w-3.5 mr-1" />
                        {sending === user.telegram_id ? "..." : "Отправить"}
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
