import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2, X, ChevronRight, Tags } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

type TopicTag = { tag: string; count: number };
type TopicItem = { id: number; name: string; tags: TopicTag[] };
type TopicsData = Record<string, TopicItem[]>;

export function Topics() {
  const [data, setData] = useState<TopicsData>({});
  const [loading, setLoading] = useState(true);

  // volumes that were created locally but have no topics yet
  const [pendingVolumes, setPendingVolumes] = useState<string[]>([]);

  const [selectedVolume, setSelectedVolume] = useState<string | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);

  const [showNewVolume, setShowNewVolume] = useState(false);
  const [newVolumeName, setNewVolumeName] = useState("");

  const [showNewTopic, setShowNewTopic] = useState(false);
  const [newTopicName, setNewTopicName] = useState("");
  const [creatingTopic, setCreatingTopic] = useState(false);

  const [newTagText, setNewTagText] = useState("");
  const [savingTags, setSavingTags] = useState(false);

  const newVolumeRef = useRef<HTMLInputElement>(null);
  const newTopicRef = useRef<HTMLInputElement>(null);
  const newTagRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getTopics()
      .then(setData)
      .catch(() => toast.error("Ошибка загрузки тем"))
      .finally(() => setLoading(false));
  }, []);

  const allVolumes = [
    ...Object.keys(data),
    ...pendingVolumes.filter((v) => !Object.keys(data).includes(v)),
  ];

  const selectedTopic = selectedTopicId
    ? Object.values(data).flat().find((t) => t.id === selectedTopicId) ?? null
    : null;

  // ── Volumes ────────────────────────────────────────────────────────────────

  const handleAddVolume = () => {
    const name = newVolumeName.trim();
    if (!name) return;
    if (allVolumes.includes(name)) {
      toast.warning("Раздел с таким именем уже существует");
      return;
    }
    setPendingVolumes((prev) => [...prev, name]);
    setSelectedVolume(name);
    setSelectedTopicId(null);
    setNewVolumeName("");
    setShowNewVolume(false);
  };

  const handleDeleteVolume = async (volume: string) => {
    const topics = data[volume] ?? [];
    try {
      await Promise.all(topics.map((t) => api.deleteTopic(t.id)));
      setData((prev) => {
        const next = { ...prev };
        delete next[volume];
        return next;
      });
      setPendingVolumes((prev) => prev.filter((v) => v !== volume));
      if (selectedVolume === volume) {
        setSelectedVolume(null);
        setSelectedTopicId(null);
      }
      toast.success("Раздел удалён");
    } catch {
      toast.error("Ошибка удаления раздела");
    }
  };

  // ── Topics ─────────────────────────────────────────────────────────────────

  const handleCreateTopic = async () => {
    const name = newTopicName.trim();
    if (!name || !selectedVolume) return;
    setCreatingTopic(true);
    try {
      const t = await api.createTopic(name, selectedVolume);
      setData((prev) => ({
        ...prev,
        [selectedVolume]: [
          ...(prev[selectedVolume] ?? []),
          { id: t.id, name: t.name, tags: [] },
        ],
      }));
      setPendingVolumes((prev) => prev.filter((v) => v !== selectedVolume));
      setSelectedTopicId(t.id);
      setNewTopicName("");
      setShowNewTopic(false);
      toast.success("Тема создана");
    } catch {
      toast.error("Ошибка создания темы");
    } finally {
      setCreatingTopic(false);
    }
  };

  const handleDeleteTopic = async (topicId: number) => {
    try {
      await api.deleteTopic(topicId);
      setData((prev) => {
        const next = { ...prev };
        for (const vol of Object.keys(next)) {
          next[vol] = next[vol].filter((t) => t.id !== topicId);
          if (next[vol].length === 0) delete next[vol];
        }
        return next;
      });
      if (selectedTopicId === topicId) setSelectedTopicId(null);
      toast.success("Тема удалена");
    } catch {
      toast.error("Ошибка удаления темы");
    }
  };

  // ── Tags ───────────────────────────────────────────────────────────────────

  const handleAddTag = async () => {
    if (!selectedTopic || !newTagText.trim()) return;
    const tag = newTagText.trim();
    if (selectedTopic.tags.some((t) => t.tag === tag)) {
      toast.warning("Такой тег уже есть");
      return;
    }
    const newTags = [...selectedTopic.tags.map((t) => t.tag), tag];
    setSavingTags(true);
    try {
      await api.updateTopicTags(selectedTopic.id, newTags);
      setData((prev) => {
        const next = { ...prev };
        for (const vol of Object.keys(next)) {
          next[vol] = next[vol].map((t) =>
            t.id === selectedTopic.id
              ? { ...t, tags: [...t.tags, { tag, count: 0 }] }
              : t
          );
        }
        return next;
      });
      setNewTagText("");
      newTagRef.current?.focus();
    } catch {
      toast.error("Ошибка сохранения тегов");
    } finally {
      setSavingTags(false);
    }
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    if (!selectedTopic) return;
    const newTags = selectedTopic.tags
      .filter((t) => t.tag !== tagToRemove)
      .map((t) => t.tag);
    setSavingTags(true);
    try {
      await api.updateTopicTags(selectedTopic.id, newTags);
      setData((prev) => {
        const next = { ...prev };
        for (const vol of Object.keys(next)) {
          next[vol] = next[vol].map((t) =>
            t.id === selectedTopic.id
              ? { ...t, tags: t.tags.filter((tag) => tag.tag !== tagToRemove) }
              : t
          );
        }
        return next;
      });
    } catch {
      toast.error("Ошибка сохранения тегов");
    } finally {
      setSavingTags(false);
    }
  };

  // ──────────────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="text-center py-12 text-[var(--color-muted-foreground)]">
        Загрузка...
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row lg:h-full lg:min-h-0 border rounded-lg overflow-hidden">
      {/* ── Column 1: Volumes ────────────────────────────────────────────── */}
      <div className="lg:w-56 shrink-0 flex flex-col min-h-0 border-b lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)]">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
            Разделы
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => {
              setShowNewVolume((v) => !v);
              setTimeout(() => newVolumeRef.current?.focus(), 50);
            }}
          >
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>

        {showNewVolume && (
          <div className="flex gap-1 px-2 py-2 border-b shrink-0">
            <Input
              ref={newVolumeRef}
              value={newVolumeName}
              onChange={(e) => setNewVolumeName(e.target.value)}
              placeholder="Название раздела"
              className="h-7 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddVolume();
                if (e.key === "Escape") setShowNewVolume(false);
              }}
            />
            <Button size="sm" className="h-7 px-2 shrink-0" onClick={handleAddVolume}>
              ✓
            </Button>
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto">
          {allVolumes.length === 0 ? (
            <p className="text-center py-6 text-xs text-[var(--color-muted-foreground)]">
              Нет разделов
            </p>
          ) : (
            allVolumes.map((volume) => (
              <div
                key={volume}
                className={`group flex items-center gap-1 px-3 py-2 cursor-pointer text-sm hover:bg-[var(--color-accent)] transition-colors ${
                  selectedVolume === volume ? "bg-[var(--color-accent)] font-medium" : ""
                }`}
                onClick={() => {
                  setSelectedVolume(volume);
                  setSelectedTopicId(null);
                  setShowNewTopic(false);
                }}
              >
                <span className="flex-1 truncate">{volume}</span>
                {pendingVolumes.includes(volume) && (
                  <span className="text-[10px] text-[var(--color-muted-foreground)] shrink-0">
                    новый
                  </span>
                )}
                <ChevronRight
                  className={`h-3.5 w-3.5 shrink-0 transition-opacity ${
                    selectedVolume === volume
                      ? "opacity-60"
                      : "opacity-0 group-hover:opacity-30"
                  }`}
                />
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <button
                      className="opacity-0 group-hover:opacity-70 hover:!opacity-100 transition-opacity hover:text-[var(--color-destructive)]"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Удалить раздел?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Удалятся все темы раздела «{volume}». Действие нельзя отменить.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Отмена</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-[var(--color-destructive)] hover:opacity-90"
                        onClick={() => handleDeleteVolume(volume)}
                      >
                        Удалить
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 2: Topics ─────────────────────────────────────────────── */}
      <div className="lg:w-64 shrink-0 flex flex-col min-h-0 border-b lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between px-3 py-2.5 border-b shrink-0 bg-[var(--color-card)]">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)] truncate">
            {selectedVolume ? selectedVolume : "Темы"}
          </span>
          {selectedVolume && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0"
              onClick={() => {
                setShowNewTopic((v) => !v);
                setTimeout(() => newTopicRef.current?.focus(), 50);
              }}
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>

        {showNewTopic && selectedVolume && (
          <div className="flex gap-1 px-2 py-2 border-b shrink-0">
            <Input
              ref={newTopicRef}
              value={newTopicName}
              onChange={(e) => setNewTopicName(e.target.value)}
              placeholder="Название темы"
              className="h-7 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreateTopic();
                if (e.key === "Escape") setShowNewTopic(false);
              }}
            />
            <Button
              size="sm"
              className="h-7 px-2 shrink-0"
              onClick={handleCreateTopic}
              disabled={creatingTopic}
            >
              ✓
            </Button>
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto">
          {!selectedVolume ? (
            <p className="text-center py-6 text-xs text-[var(--color-muted-foreground)]">
              Выберите раздел
            </p>
          ) : (data[selectedVolume] ?? []).length === 0 ? (
            <p className="text-center py-6 text-xs text-[var(--color-muted-foreground)]">
              Нет тем — нажмите + чтобы создать
            </p>
          ) : (
            (data[selectedVolume] ?? []).map((topic) => (
              <div
                key={topic.id}
                className={`group flex items-center gap-1 px-3 py-2 cursor-pointer text-sm hover:bg-[var(--color-accent)] transition-colors ${
                  selectedTopicId === topic.id
                    ? "bg-[var(--color-accent)] font-medium"
                    : ""
                }`}
                onClick={() => setSelectedTopicId(topic.id)}
              >
                <span className="flex-1 truncate">{topic.name}</span>
                <span className="text-xs text-[var(--color-muted-foreground)] shrink-0">
                  {topic.tags.length}
                </span>
                <ChevronRight
                  className={`h-3.5 w-3.5 shrink-0 transition-opacity ${
                    selectedTopicId === topic.id
                      ? "opacity-60"
                      : "opacity-0 group-hover:opacity-30"
                  }`}
                />
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <button
                      className="opacity-0 group-hover:opacity-70 hover:!opacity-100 transition-opacity hover:text-[var(--color-destructive)]"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Удалить тему?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Тема «{topic.name}» и все её теги будут удалены.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Отмена</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-[var(--color-destructive)] hover:opacity-90"
                        onClick={() => handleDeleteTopic(topic.id)}
                      >
                        Удалить
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Column 3: Tags ───────────────────────────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col min-h-0">
        <div className="px-4 py-2.5 border-b shrink-0 bg-[var(--color-card)]">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
            {selectedTopic ? selectedTopic.name : "Теги"}
          </span>
          {selectedTopic && (
            <span className="text-xs text-[var(--color-muted-foreground)] ml-2">
              — {selectedTopic.tags.length} тегов
            </span>
          )}
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto p-4">
          {!selectedTopic ? (
            <div className="flex flex-col items-center justify-center h-full py-16 text-[var(--color-muted-foreground)]">
              <Tags className="h-12 w-12 mb-3 opacity-20" />
              <p className="text-sm">Выберите тему для редактирования тегов</p>
            </div>
          ) : (
            <div className="space-y-4 max-w-lg">
              {/* Add tag */}
              <div className="flex gap-2">
                <Input
                  ref={newTagRef}
                  value={newTagText}
                  onChange={(e) => setNewTagText(e.target.value)}
                  placeholder="Новый тег..."
                  className="h-8 text-sm"
                  disabled={savingTags}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleAddTag();
                  }}
                />
                <Button
                  size="sm"
                  className="h-8 shrink-0"
                  onClick={handleAddTag}
                  disabled={savingTags || !newTagText.trim()}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Добавить
                </Button>
              </div>

              {/* Tags chips */}
              {selectedTopic.tags.length === 0 ? (
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  Нет тегов — добавьте первый выше
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selectedTopic.tags.map(({ tag, count }) => (
                    <div
                      key={tag}
                      className="flex items-center gap-1.5 bg-[var(--color-accent)] rounded-full px-3 py-1 text-sm"
                    >
                      <span>{tag}</span>
                      <span className="text-xs text-[var(--color-muted-foreground)]">
                        ({count})
                      </span>
                      <button
                        className="ml-0.5 hover:text-[var(--color-destructive)] transition-colors disabled:opacity-40"
                        onClick={() => handleRemoveTag(tag)}
                        disabled={savingTags}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
