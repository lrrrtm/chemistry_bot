import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Search, Database, Save, Trash2, Upload, X, Download, Plus, ChevronLeft, BookPlus, FileSpreadsheet } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";

type QuestionFull = {
  id: number;
  text: string;
  answer: string;
  level: number;
  full_mark: number;
  tags_list: string[];
  is_rotate: number;
  is_selfcheck: number;
  question_image: boolean;
  answer_image: boolean;
  type: string;
};

type PoolItem = { id: number; text: string; tags_list: string[] };

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function PoolPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const autoOpenId = (location.state as { openQuestionId?: number } | null)?.openQuestionId;
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selected, setSelected] = useState<QuestionFull | null>(null);
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [saving, setSaving] = useState(false);
  const [edited, setEdited] = useState<Partial<QuestionFull>>({});
  const [newTagInput, setNewTagInput] = useState("");
  const newTagRef = useRef<HTMLInputElement>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);
  const importFileRef = useRef<HTMLInputElement>(null);

  // Mobile step: 0 = question list, 1 = question editor
  const [mobileStep, setMobileStep] = useState<0 | 1>(0);

  useEffect(() => {
    api.getPool()
      .then(setPool)
      .catch(() => toast.error("Ошибка загрузки пула вопросов"))
      .finally(() => setLoading(false));
  }, []);

  // Auto-open question when navigated from another page with openQuestionId state
  useEffect(() => {
    if (!loading && autoOpenId) {
      setSearch(String(autoOpenId));
      openQuestion(autoOpenId);
      window.history.replaceState({}, "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const filtered = pool.filter((q) => {
    const s = search.toLowerCase();
    return (
      String(q.id).includes(s) ||
      q.text.toLowerCase().includes(s) ||
      q.tags_list.some((t) => t.toLowerCase().includes(s))
    );
  });

  const openQuestion = async (id: number) => {
    if (id === selectedId) return;
    setSelectedId(id);
    setSelected(null);
    setLoadingQuestion(true);
    setNewTagInput("");
    setMobileStep(1);
    scrollToTop();
    try {
      const q = await api.getQuestion(id);
      setSelected(q);
      setEdited({ ...q });
    } catch {
      toast.error("Ошибка загрузки вопроса");
      setSelectedId(null);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.updateQuestion(selected.id, {
        text: edited.text ?? selected.text,
        answer: edited.answer ?? selected.answer,
        level: edited.level ?? selected.level,
        full_mark: edited.full_mark ?? selected.full_mark,
        tags_list: edited.tags_list ?? selected.tags_list,
        is_rotate: edited.is_rotate ?? selected.is_rotate,
        is_selfcheck: edited.is_selfcheck ?? selected.is_selfcheck,
      });
      toast.success("Вопрос обновлён");
      // Sync updated text/tags back to the list
      const newTags = edited.tags_list ?? selected.tags_list;
      const newText = edited.text ?? selected.text;
      setPool((p) =>
        p.map((q) => q.id === selected.id ? { ...q, text: newText, tags_list: newTags } : q)
      );
    } catch {
      toast.error("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      await api.deleteQuestion(selected.id);
      toast.success("Вопрос удалён");
      setPool((p) => p.filter((q) => q.id !== selected.id));
      setSelected(null);
      setSelectedId(null);
      setMobileStep(0);
      scrollToTop();
    } catch {
      toast.error("Ошибка удаления");
    }
  };

  const uploadImage = async (type: "question" | "answer", file: File) => {
    if (!selected) return;
    try {
      if (type === "question") await api.uploadQuestionImage(selected.id, file);
      else await api.uploadAnswerImage(selected.id, file);
      toast.success("Изображение загружено");
      const updated = await api.getQuestion(selected.id);
      setSelected(updated);
      setEdited({ ...updated });
    } catch {
      toast.error("Ошибка загрузки изображения");
    }
  };

  const removeImage = async (type: "question" | "answer") => {
    if (!selected) return;
    try {
      if (type === "question") await api.deleteQuestionImage(selected.id);
      else await api.deleteAnswerImage(selected.id);
      toast.success("Изображение удалено");
      const updated = await api.getQuestion(selected.id);
      setSelected(updated);
      setEdited({ ...updated });
    } catch {
      toast.error("Ошибка удаления изображения");
    }
  };

  const ImageSection = ({ type, hasImage }: { type: "question" | "answer"; hasImage: boolean }) => (
    <div className="space-y-2">
      <Label>{type === "question" ? "Изображение вопроса" : "Изображение ответа"}</Label>
      {hasImage ? (
        <div className="relative rounded-lg overflow-hidden border">
          <img
            src={type === "question" ? api.imageUrl.question(selected!.id) : api.imageUrl.answer(selected!.id)}
            alt={type}
            className="w-full max-h-48 object-contain"
          />
          <button
            className="absolute top-1.5 right-1.5 bg-black/60 text-white rounded-full p-0.5 hover:bg-black/80"
            onClick={() => removeImage(type)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : null}
      <label>
        <input
          type="file"
          accept="image/png"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && uploadImage(type, e.target.files[0])}
        />
        <div
          className="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:border-[var(--color-primary)] transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files[0];
            if (f && f.type === "image/png") uploadImage(type, f);
          }}
        >
          <Upload className="h-6 w-6 mx-auto text-[var(--color-muted-foreground)] mb-1" />
          <p className="text-xs text-[var(--color-muted-foreground)]">
            {hasImage ? "Перетащите PNG или нажмите для замены" : "Перетащите PNG или нажмите для загрузки"}
          </p>
        </div>
      </label>
    </div>
  );

  if (loading) return <div className="text-center py-12 text-[var(--color-muted-foreground)]">Загрузка...</div>;

  function scrollToTop() {
    document.querySelector("main")?.scrollTo(0, 0);
  }

  return (
    <div className="flex flex-col lg:flex-row lg:h-full lg:min-h-0 border rounded-lg overflow-hidden">
      {/* Left panel — question list */}
      <div className={`${mobileStep !== 0 ? "hidden lg:flex" : "flex"} flex-col lg:w-80 shrink-0 min-h-0 border-b lg:border-b-0 lg:border-r`}>
        {/* Header */}
        <div className="px-4 pt-4 pb-2 border-b shrink-0 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-sm">Пул вопросов</h2>
              <p className="text-xs text-[var(--color-muted-foreground)]">{pool.length} активных</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs gap-1"
              onClick={() => setAddDialogOpen(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              Добавить
            </Button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--color-muted-foreground)]" />
            <Input
              placeholder="ID, текст или тег..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-8 text-sm"
            />
          </div>
        </div>

        {/* Question list */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="text-center py-12 text-[var(--color-muted-foreground)]">
              <Database className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Вопросы не найдены</p>
            </div>
          ) : (
            <>
              {filtered.slice(0, 100).map((q) => (
                <button
                  key={q.id}
                  className={`w-full text-left flex items-start gap-2 px-3 py-2.5 cursor-pointer hover:bg-[var(--color-accent)] transition-colors border-b last:border-b-0 ${
                    selectedId === q.id ? "bg-[var(--color-accent)]" : ""
                  }`}
                  onClick={() => openQuestion(q.id)}
                >
                  <Badge variant="outline" className="shrink-0 mt-0.5 text-xs">
                    {q.id}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm line-clamp-2">{q.text || <span className="text-[var(--color-muted-foreground)] italic">Вопрос на картинке</span>}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {q.tags_list.slice(0, 3).map((t) => (
                        <Badge key={t} variant="secondary" className="text-xs px-1.5 py-0">{t}</Badge>
                      ))}
                      {q.tags_list.length > 3 && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">+{q.tags_list.length - 3}</Badge>
                      )}
                    </div>
                  </div>
                </button>
              ))}
              {filtered.length > 100 && (
                <p className="text-center text-xs text-[var(--color-muted-foreground)] py-3 px-3">
                  Первые 100 из {filtered.length}. Уточните поиск.
                </p>
              )}
            </>
          )}
        </div>
      </div>

      {/* Right panel — question editor */}
      <div className={`${mobileStep !== 1 ? "hidden lg:flex" : "flex"} flex-col flex-1 min-w-0 min-h-0`}>
        {/* Mobile back bar */}
        <div className="flex items-center gap-2 px-3 py-2 border-b shrink-0 bg-[var(--color-card)] lg:hidden">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1 h-7 px-2 text-xs"
            onClick={() => { setMobileStep(0); scrollToTop(); }}
          >
            <ChevronLeft className="h-4 w-4" />
            К списку
          </Button>
        </div>
        {loadingQuestion ? (
          <div className="flex-1 flex items-center justify-center text-[var(--color-muted-foreground)]">
            <p className="text-sm">Загрузка вопроса...</p>
          </div>
        ) : !selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-muted-foreground)] gap-2">
            <Database className="h-12 w-12 opacity-20" />
            <p className="text-sm">Выберите вопрос из списка</p>
          </div>
        ) : (
          <>
            {/* Editor header */}
            <div className="px-5 py-3 border-b shrink-0 flex items-center justify-between">
              <div>
                <span className="font-semibold text-sm">Вопрос id{selected.id}</span>
                <span className="ml-2 text-xs text-[var(--color-muted-foreground)]">{selected.type}</span>
              </div>
              <div className="flex gap-2">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" size="sm" className="h-7 text-xs">
                      <Trash2 className="h-3.5 w-3.5 mr-1" />
                      Удалить
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Удалить вопрос?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Вопрос id{selected.id} будет деактивирован.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Отмена</AlertDialogCancel>
                      <AlertDialogAction onClick={handleDelete} className="bg-[var(--color-destructive)]">
                        Удалить
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
                <Button size="sm" className="h-7 text-xs" onClick={handleSave} disabled={saving}>
                  <Save className="h-3.5 w-3.5 mr-1" />
                  {saving ? "Сохранение..." : "Сохранить"}
                </Button>
              </div>
            </div>

            {/* Editor form */}
            <div className="flex-1 min-h-0 overflow-y-auto">
              <CardContent className="py-4 space-y-4">
                {/* Question text */}
                <div className="space-y-2">
                  <Label>Текст вопроса</Label>
                  <Textarea
                    value={edited.text ?? selected.text}
                    onChange={(e) => setEdited((p) => ({ ...p, text: e.target.value }))}
                    rows={20}
                  />
                </div>

                <ImageSection type="question" hasImage={selected.question_image} />

                {/* Answer text */}
                <div className="space-y-2">
                  <Label>Текст ответа</Label>
                  <Textarea
                    value={edited.answer ?? selected.answer}
                    onChange={(e) => setEdited((p) => ({ ...p, answer: e.target.value }))}
                    rows={20}
                  />
                </div>

                <ImageSection type="answer" hasImage={selected.answer_image} />

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>Сложность (1–5)</Label>
                    <Select
                      value={String(edited.level ?? selected.level)}
                      onValueChange={(v) => setEdited((p) => ({ ...p, level: Number(v) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
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
                      value={String(edited.full_mark ?? selected.full_mark)}
                      onValueChange={(v) => setEdited((p) => ({ ...p, full_mark: Number(v) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
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
                  {/* Add tag input */}
                  <div className="flex gap-2">
                    <Input
                      ref={newTagRef}
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                      placeholder="Новый тег..."
                      className="h-8 text-sm"
                      onKeyDown={(e) => {
                        if (e.key !== "Enter") return;
                        const tag = newTagInput.trim();
                        if (!tag) return;
                        const current = edited.tags_list ?? selected.tags_list;
                        if (current.includes(tag)) {
                          toast.warning("Такой тег уже есть");
                          return;
                        }
                        setEdited((p) => ({ ...p, tags_list: [...current, tag] }));
                        setNewTagInput("");
                        newTagRef.current?.focus();
                      }}
                    />
                    <Button
                      size="sm"
                      className="h-8 shrink-0"
                      disabled={!newTagInput.trim()}
                      onClick={() => {
                        const tag = newTagInput.trim();
                        if (!tag) return;
                        const current = edited.tags_list ?? selected.tags_list;
                        if (current.includes(tag)) {
                          toast.warning("Такой тег уже есть");
                          return;
                        }
                        setEdited((p) => ({ ...p, tags_list: [...current, tag] }));
                        setNewTagInput("");
                        newTagRef.current?.focus();
                      }}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Добавить
                    </Button>
                  </div>
                  {/* Tag chips */}
                  {(edited.tags_list ?? selected.tags_list).length === 0 ? (
                    <p className="text-sm text-[var(--color-muted-foreground)]">Нет тегов</p>
                  ) : (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {(edited.tags_list ?? selected.tags_list).map((tag) => (
                        <div
                          key={tag}
                          className="flex items-center gap-1.5 bg-[var(--color-accent)] rounded-full px-3 py-1 text-sm"
                        >
                          <span>{tag}</span>
                          <button
                            className="ml-0.5 hover:text-[var(--color-destructive)] transition-colors"
                            onClick={() =>
                              setEdited((p) => ({
                                ...p,
                                tags_list: (p.tags_list ?? selected!.tags_list).filter((t) => t !== tag),
                              }))
                            }
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
                      checked={Boolean(edited.is_rotate ?? selected.is_rotate)}
                      onCheckedChange={(v) => setEdited((p) => ({ ...p, is_rotate: Number(v) }))}
                    />
                    <Label>Вращение ответа</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={Boolean(edited.is_selfcheck ?? selected.is_selfcheck)}
                      onCheckedChange={(v) => setEdited((p) => ({ ...p, is_selfcheck: Number(v) }))}
                    />
                    <Label>Самопроверка</Label>
                  </div>
                </div>
              </CardContent>
            </div>
          </>
        )}
      </div>

      {/* Add question dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Добавить вопросы</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => { setAddDialogOpen(false); navigate("/admin/add-question"); }}
            >
              <BookPlus className="h-4 w-4" />
              Создать вопрос вручную
            </Button>

            <div className="relative flex items-center gap-3 py-2">
              <div className="flex-1 border-t border-[var(--color-border)]" />
              <span className="text-xs text-[var(--color-muted-foreground)]">или через Excel</span>
              <div className="flex-1 border-t border-[var(--color-border)]" />
            </div>

            <Button
              variant="outline"
              className="w-full justify-start"
              disabled={downloadingTemplate}
              onClick={async () => {
                setDownloadingTemplate(true);
                try {
                  const blob = await api.getPoolTemplate();
                  downloadBlob(blob, "chembot_pool_list.xlsx");
                } catch {
                  toast.error("Ошибка скачивания шаблона");
                } finally {
                  setDownloadingTemplate(false);
                }
              }}
            >
              <Download className="h-4 w-4" />
              {downloadingTemplate ? "Скачивание..." : "Скачать шаблон"}
            </Button>

            <div className="space-y-2">
              <Input
                ref={importFileRef}
                type="file"
                accept=".xlsx"
                className="text-sm"
                onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
              />
              <Button
                className="w-full"
                disabled={importing || !importFile}
                onClick={async () => {
                  if (!importFile) return;
                  setImporting(true);
                  try {
                    const result = await api.importPoolExcel(importFile);
                    toast.success(result.message);
                    setImportFile(null);
                    if (importFileRef.current) importFileRef.current.value = "";
                    const updatedPool = await api.getPool();
                    setPool(updatedPool);
                    setAddDialogOpen(false);
                  } catch (e) {
                    toast.error(e instanceof Error ? e.message : "Ошибка импорта");
                  } finally {
                    setImporting(false);
                  }
                }}
              >
                <FileSpreadsheet className="h-4 w-4" />
                {importing ? "Импорт..." : "Импортировать Excel"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
