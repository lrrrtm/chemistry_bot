import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Search, Database, Save, Trash2, Upload, X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

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

export function PoolPage() {
  const [pool, setPool] = useState<PoolItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<QuestionFull | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [edited, setEdited] = useState<Partial<QuestionFull>>({});

  useEffect(() => {
    api.getPool()
      .then(setPool)
      .catch(() => toast.error("Ошибка загрузки пула вопросов"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = pool.filter((q) => {
    const s = search.toLowerCase();
    return (
      String(q.id).includes(s) ||
      q.text.toLowerCase().includes(s) ||
      q.tags_list.some((t) => t.toLowerCase().includes(s))
    );
  });

  const openQuestion = async (id: number) => {
    try {
      const q = await api.getQuestion(id);
      setSelected(q);
      setEdited({ ...q });
      setDialogOpen(true);
    } catch {
      toast.error("Ошибка загрузки вопроса");
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
      setDialogOpen(false);
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
      setDialogOpen(false);
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
      {hasImage && (
        <div className="relative">
          <img
            src={type === "question" ? api.imageUrl.question(selected!.id) : api.imageUrl.answer(selected!.id)}
            alt={type}
            className="w-full max-h-48 object-contain rounded-lg border"
          />
        </div>
      )}
      <div className="flex gap-2">
        <label className="flex-1">
          <input
            type="file"
            accept="image/png"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && uploadImage(type, e.target.files[0])}
          />
          <Button variant="outline" size="sm" className="w-full" asChild>
            <span>
              <Upload className="h-3 w-3 mr-1.5" />
              {hasImage ? "Заменить" : "Загрузить"}
            </span>
          </Button>
        </label>
        {hasImage && (
          <Button variant="outline" size="sm" onClick={() => removeImage(type)}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
    </div>
  );

  if (loading) return <div className="text-center py-12 text-[var(--color-muted-foreground)]">Загрузка...</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Пул вопросов</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
          {pool.length} активных вопросов
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-muted-foreground)]" />
        <Input
          placeholder="Поиск по ID, тексту или тегу..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-[var(--color-muted-foreground)]">
          <Database className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>Вопросы не найдены</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.slice(0, 100).map((q) => (
            <Card
              key={q.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => openQuestion(q.id)}
            >
              <CardContent className="py-3 px-4">
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="shrink-0 mt-0.5">
                    id{q.id}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm line-clamp-2">{q.text}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {q.tags_list.slice(0, 4).map((t) => (
                        <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
                      ))}
                      {q.tags_list.length > 4 && (
                        <Badge variant="secondary" className="text-xs">+{q.tags_list.length - 4}</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {filtered.length > 100 && (
            <p className="text-center text-sm text-[var(--color-muted-foreground)]">
              Показаны первые 100 из {filtered.length}. Уточните поиск.
            </p>
          )}
        </div>
      )}

      {/* Question edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Вопрос id{selected?.id}</DialogTitle>
          </DialogHeader>

          {selected && (
            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
              {/* Question text */}
              <div className="space-y-2">
                <Label>Текст вопроса</Label>
                <Textarea
                  value={edited.text ?? selected.text}
                  onChange={(e) => setEdited((p) => ({ ...p, text: e.target.value }))}
                  rows={3}
                />
              </div>

              <ImageSection type="question" hasImage={selected.question_image} />

              {/* Answer text */}
              <div className="space-y-2">
                <Label>Текст ответа</Label>
                <Textarea
                  value={edited.answer ?? selected.answer}
                  onChange={(e) => setEdited((p) => ({ ...p, answer: e.target.value }))}
                  rows={2}
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
                <Label>Теги (по одному на строку)</Label>
                <Textarea
                  value={(edited.tags_list ?? selected.tags_list).join("\n")}
                  onChange={(e) => setEdited((p) => ({ ...p, tags_list: e.target.value.split("\n").filter(Boolean) }))}
                  rows={4}
                  className="font-mono text-xs"
                />
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

              <div className="flex gap-3 pt-2">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" size="sm">
                      <Trash2 className="h-4 w-4 mr-1" />
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

                <Button className="flex-1" onClick={handleSave} disabled={saving}>
                  <Save className="h-4 w-4 mr-1" />
                  {saving ? "Сохранение..." : "Сохранить"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
