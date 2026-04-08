import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/SearchInput";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AdminTopicsTree } from "@/lib/types";

type TagHierarchySelectorProps = {
  value: string[];
  onChange: (next: string[]) => void;
  className?: string;
  disabled?: boolean;
};

function uniqueTags(tags: string[]) {
  return Array.from(new Set(tags.filter(Boolean)));
}

export function TagHierarchySelector({
  value,
  onChange,
  className,
  disabled = false,
}: TagHierarchySelectorProps) {
  const [topicsTree, setTopicsTree] = useState<AdminTopicsTree>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let active = true;

    api.getTopics()
      .then((data) => {
        if (!active) return;
        setTopicsTree(data);
        setLoadError(null);
      })
      .catch(() => {
        if (!active) return;
        setLoadError("Не удалось загрузить структуру тегов");
        toast.error("Ошибка загрузки структуры тегов");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedTags = uniqueTags(value);
  const selectedSet = new Set(selectedTags);
  const availableTags = uniqueTags(
    Object.values(topicsTree)
      .flat()
      .flatMap((topic) => topic.tags.map(({ tag }) => tag))
  );
  const availableSet = new Set(availableTags);
  const orphanTags = selectedTags.filter((tag) => !availableSet.has(tag));
  const normalizedSearch = search.trim().toLowerCase();
  const autoExpandedSections = useMemo(
    () =>
      new Set(
        Object.entries(topicsTree)
          .filter(([, topics]) =>
            topics.some((topic) => topic.tags.some(({ tag }) => selectedSet.has(tag)))
          )
          .map(([volume]) => volume)
      ),
    [selectedSet, topicsTree]
  );

  const setNextTags = (next: string[]) => {
    onChange(uniqueTags(next));
  };

  const toggleTag = (tag: string, checked: boolean) => {
    if (checked) {
      setNextTags([...selectedTags, tag]);
      return;
    }
    setNextTags(selectedTags.filter((item) => item !== tag));
  };

  const toggleTopic = (topicTags: string[], checked: boolean) => {
    if (topicTags.length === 0) return;
    if (checked) {
      setNextTags([...selectedTags, ...topicTags]);
      return;
    }
    const topicTagSet = new Set(topicTags);
    setNextTags(selectedTags.filter((tag) => !topicTagSet.has(tag)));
  };

  const sectionEntries = Object.entries(topicsTree);
  const filteredSectionEntries = sectionEntries
    .map(([volume, topics]) => {
      if (!normalizedSearch) {
        return [volume, topics] as const;
      }

      const volumeMatches = volume.toLowerCase().includes(normalizedSearch);
      const filteredTopics = topics.filter((topic) => {
        if (volumeMatches) return true;
        if (topic.name.toLowerCase().includes(normalizedSearch)) return true;
        return topic.tags.some(({ tag }) => tag.toLowerCase().includes(normalizedSearch));
      });

      return [volume, filteredTopics] as const;
    })
    .filter(([, topics]) => topics.length > 0);

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-[var(--color-card)] px-4 py-3">
        <div>
          <p className="text-sm font-medium">Разделы, темы и теги</p>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Отметьте нужные теги или целиком тему
          </p>
        </div>
        <Badge variant="secondary" className="text-xs">
          Выбрано: {selectedTags.length}
        </Badge>
      </div>

      <SearchInput
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Поиск по темам и тегам..."
        className="h-9"
      />

      {loading ? (
        <div className="rounded-lg border border-dashed px-4 py-6 text-sm text-[var(--color-muted-foreground)]">
          Загружаем доступные теги...
        </div>
      ) : loadError ? (
        <div className="rounded-lg border border-dashed px-4 py-6 text-sm text-[var(--color-destructive)]">
          {loadError}
        </div>
      ) : sectionEntries.length === 0 ? (
        <div className="rounded-lg border border-dashed px-4 py-6 text-sm text-[var(--color-muted-foreground)]">
          Разделы и темы пока не настроены. Сначала добавьте теги в разделе тем.
        </div>
      ) : filteredSectionEntries.length === 0 ? (
        <div className="rounded-lg border border-dashed px-4 py-6 text-sm text-[var(--color-muted-foreground)]">
          Ничего не найдено по текущему запросу.
        </div>
      ) : (
        filteredSectionEntries.map(([volume, topics]) => {
          const sectionTags = uniqueTags(
            topics.flatMap((topic) => topic.tags.map(({ tag }) => tag))
          );
          const sectionSelectedCount = sectionTags.filter((tag) => selectedSet.has(tag)).length;
          const isAutoExpanded = normalizedSearch.length > 0 || autoExpandedSections.has(volume);

          return (
            <details
              key={`${volume}-${normalizedSearch || "default"}`}
              open={isAutoExpanded ? true : undefined}
              className="group overflow-hidden rounded-lg border bg-[var(--color-card)]"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
                <div className="flex min-w-0 items-start gap-2">
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-muted-foreground)] transition-transform group-open:rotate-90" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{volume}</p>
                    <p className="text-xs text-[var(--color-muted-foreground)]">
                      Тем: {topics.length}, тегов: {sectionTags.length}
                    </p>
                  </div>
                </div>
                <Badge variant="outline" className="text-xs">
                  {sectionSelectedCount}/{sectionTags.length}
                </Badge>
              </summary>

              <div className="space-y-3 border-t px-3 py-3">
                {topics.map((topic) => {
                  const topicTags = topic.tags.map(({ tag }) => tag);
                  const selectedCount = topicTags.filter((tag) => selectedSet.has(tag)).length;
                  const allSelected = topicTags.length > 0 && selectedCount === topicTags.length;

                  return (
                    <div key={topic.id} className="rounded-md border bg-[var(--color-background)] p-3">
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={allSelected}
                          disabled={disabled || topicTags.length === 0}
                          onChange={(event) => toggleTopic(topicTags, event.target.checked)}
                          className="mt-1 h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
                        />

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-medium">{topic.name}</p>
                            <Badge variant="secondary" className="text-[10px]">
                              {selectedCount}/{topicTags.length}
                            </Badge>
                          </div>

                          {topic.tags.length === 0 ? (
                            <p className="mt-2 text-xs text-[var(--color-muted-foreground)]">
                              У этой темы пока нет тегов
                            </p>
                          ) : (
                            <div className="mt-3 grid gap-2 sm:grid-cols-2">
                              {topic.tags.map(({ tag, count }) => (
                                <label
                                  key={`${topic.id}-${tag}`}
                                  className={cn(
                                    "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors",
                                    selectedSet.has(tag)
                                      ? "border-[var(--color-primary)] bg-[var(--color-accent)]"
                                      : "hover:bg-[var(--color-accent)]",
                                    disabled && "cursor-not-allowed opacity-60"
                                  )}
                                >
                                  <input
                                    type="checkbox"
                                    checked={selectedSet.has(tag)}
                                    disabled={disabled}
                                    onChange={(event) => toggleTag(tag, event.target.checked)}
                                    className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
                                  />
                                  <span className="min-w-0 flex-1 break-words">{tag}</span>
                                  <span className="shrink-0 text-xs text-[var(--color-muted-foreground)]">
                                    {count}
                                  </span>
                                </label>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </details>
          );
        })
      )}

      {orphanTags.length > 0 ? (
        <div className="rounded-lg border border-amber-300/60 bg-amber-50/60 px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-amber-900">Теги вне тем</p>
            <Badge variant="outline" className="border-amber-400/70 text-[10px] text-amber-900">
              {orphanTags.length}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-amber-900/80">
            Эти теги уже были у вопроса, но сейчас не привязаны ни к одной теме.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {orphanTags.map((tag) => (
              <label
                key={tag}
                className="flex cursor-pointer items-center gap-2 rounded-full border border-amber-300 bg-white px-3 py-1.5 text-sm text-amber-950"
              >
                <input
                  type="checkbox"
                  checked
                  disabled={disabled}
                  onChange={(event) => toggleTag(tag, event.target.checked)}
                  className="h-4 w-4 rounded border-amber-400 accent-[var(--color-primary)]"
                />
                <span>{tag}</span>
              </label>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
