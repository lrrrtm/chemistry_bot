import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Send, Filter, ChevronDown, ChevronRight, Plus, Minus } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
  const [workName, setWorkName] = useState(() => `Тренировка ${new Date().toLocaleDateString("ru-RU")}`);
  const [questionCounts, setQuestionCounts] = useState<QuestionCounts>({});
  const [expandedVolumes, setExpandedVolumes] = useState<Set<string>>(new Set());

  // Hard filter mode state
  const [hardName, setHardName] = useState(() => `Тренировка ${new Date().toLocaleDateString("ru-RU")} (фильтр)`);
  const [hardTags, setHardTags] = useState<string[]>(["", "", "", "", ""]);
  const [hardCount, setHardCount] = useState(10);

  useEffect(() => {
    api.getTopics()
      .then((data) => {
        setTopics(data);
        setExpandedVolumes(new Set(Object.keys(data)));
      })
      .catch(() => toast.error("Ошибка загрузки тем"))
      .finally(() => setLoading(false));
  }, []);

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
        name: workName || `Тренировка ${new Date().toLocaleDateString("ru-RU")}`,
        questions: questionCounts,
        mode: "tags",
      });
      toast.success(`Тренировка создана! Ссылка отправлена в Telegram.`);
      if (result.link) {
        navigator.clipboard.writeText(result.link).catch(() => {});
      }
      setQuestionCounts({});
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
      toast.success(`Тренировка создана! Ссылка отправлена в Telegram.`);
      if (result.link) {
        navigator.clipboard.writeText(result.link).catch(() => {});
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка создания тренировки");
    } finally {
      setSubmitting(false);
    }
  };

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
          <TabsTrigger value="hard" className="flex-1 sm:flex-none">Жёсткий фильтр</TabsTrigger>
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
                <CardHeader className="pb-3">
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
                              <button
                                className="h-6 w-6 rounded-full flex items-center justify-center border hover:bg-[var(--color-muted)] transition-colors"
                                onClick={() => updateCount(tag, (questionCounts[tag] ?? 0) - 1)}
                              >
                                <Minus className="h-3 w-3" />
                              </button>
                              <span className="w-7 text-center text-sm font-medium">
                                {questionCounts[tag] ?? 0}
                              </span>
                              <button
                                className="h-6 w-6 rounded-full flex items-center justify-center border hover:bg-[var(--color-muted)] transition-colors"
                                onClick={() => updateCount(tag, (questionCounts[tag] ?? 0) + 1)}
                              >
                                <Plus className="h-3 w-3" />
                              </button>
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
                {hardTags.map((tag, i) => (
                  <Input
                    key={i}
                    value={tag}
                    placeholder={`Тег №${i + 1}`}
                    onChange={(e) => {
                      const next = [...hardTags];
                      next[i] = e.target.value;
                      setHardTags(next);
                    }}
                  />
                ))}
              </div>

              <Button className="w-full" onClick={handleCreateHardFilter} disabled={submitting}>
                <Send className="h-4 w-4 mr-2" />
                {submitting ? "Создание..." : "Создать тренировку"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
