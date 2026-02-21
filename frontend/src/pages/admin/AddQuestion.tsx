import { useState } from "react";
import { toast } from "sonner";
import { Save, Upload, X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

interface FormData {
  text: string;
  answer: string;
  type: string;
  level: number;
  full_mark: number;
  tags_list: string;
  is_rotate: boolean;
  is_selfcheck: boolean;
}

const DEFAULT_FORM: FormData = {
  text: "",
  answer: "",
  type: "ege",
  level: 1,
  full_mark: 1,
  tags_list: "",
  is_rotate: false,
  is_selfcheck: false,
};

export function AddQuestion() {
  const [form, setForm] = useState<FormData>(DEFAULT_FORM);
  const [questionImg, setQuestionImg] = useState<File | null>(null);
  const [answerImg, setAnswerImg] = useState<File | null>(null);
  const [questionPreview, setQuestionPreview] = useState<string | null>(null);
  const [answerPreview, setAnswerPreview] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const update = <K extends keyof FormData>(key: K, value: FormData[K]) =>
    setForm((p) => ({ ...p, [key]: value }));

  const handleImageSelect = (type: "question" | "answer", file: File) => {
    const url = URL.createObjectURL(file);
    if (type === "question") {
      setQuestionImg(file);
      setQuestionPreview(url);
    } else {
      setAnswerImg(file);
      setAnswerPreview(url);
    }
  };

  const clearImage = (type: "question" | "answer") => {
    if (type === "question") {
      setQuestionImg(null);
      if (questionPreview) URL.revokeObjectURL(questionPreview);
      setQuestionPreview(null);
    } else {
      setAnswerImg(null);
      if (answerPreview) URL.revokeObjectURL(answerPreview);
      setAnswerPreview(null);
    }
  };

  const handleSave = async () => {
    if (!form.text.trim()) { toast.warning("Введите текст вопроса"); return; }
    if (!form.answer.trim()) { toast.warning("Введите текст ответа"); return; }
    if (!form.type) { toast.warning("Выберите тип вопроса"); return; }

    const tags = form.tags_list.split("\n").map((t) => t.trim().toLowerCase().replace("ё", "е")).filter(Boolean);
    if (tags.length === 0) { toast.warning("Добавьте хотя бы один тег"); return; }

    setSaving(true);
    try {
      const result = await api.addQuestion({
        text: form.text.trim(),
        answer: form.answer.trim(),
        type: form.type,
        level: form.level,
        full_mark: form.full_mark,
        tags_list: tags,
        is_rotate: form.is_rotate,
        is_selfcheck: form.is_selfcheck,
      });

      if (questionImg) await api.uploadQuestionImage(result.id, questionImg);
      if (answerImg) await api.uploadAnswerImage(result.id, answerImg);

      toast.success(`Вопрос id${result.id} успешно добавлен!`);
      setForm(DEFAULT_FORM);
      clearImage("question");
      clearImage("answer");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Ошибка добавления вопроса");
    } finally {
      setSaving(false);
    }
  };

  const ImageUpload = ({ type, file, preview }: { type: "question" | "answer"; file: File | null; preview: string | null }) => (
    <div className="space-y-2">
      <Label>{type === "question" ? "Изображение вопроса" : "Изображение ответа"}</Label>
      {preview && (
        <div className="relative rounded-lg overflow-hidden border">
          <img src={preview} alt="preview" className="w-full max-h-40 object-contain" />
          <button
            className="absolute top-1.5 right-1.5 bg-black/60 text-white rounded-full p-0.5 hover:bg-black/80"
            onClick={() => clearImage(type)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      <label>
        <input
          type="file"
          accept="image/png"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleImageSelect(type, e.target.files[0])}
        />
        <Button variant="outline" size="sm" className="w-full" asChild>
          <span>
            <Upload className="h-3.5 w-3.5 mr-2" />
            {file ? "Заменить PNG" : "Загрузить PNG"}
          </span>
        </Button>
      </label>
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Добавить вопрос</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
          Создайте новый вопрос в пуле
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Question */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Вопрос</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="q-text">Текст вопроса</Label>
              <Textarea
                id="q-text"
                value={form.text}
                onChange={(e) => update("text", e.target.value)}
                placeholder="Введите текст вопроса"
                rows={4}
              />
            </div>
            <ImageUpload type="question" file={questionImg} preview={questionPreview} />
          </CardContent>
        </Card>

        {/* Answer */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Ответ</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="q-answer">Текст ответа</Label>
              <Textarea
                id="q-answer"
                value={form.answer}
                onChange={(e) => update("answer", e.target.value)}
                placeholder="Введите текст ответа"
                rows={4}
              />
            </div>
            <ImageUpload type="answer" file={answerImg} preview={answerPreview} />
          </CardContent>
        </Card>
      </div>

      {/* Settings */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Параметры</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Тип вопроса</Label>
              <Select value={form.type} onValueChange={(v) => update("type", v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ege">КИМ ЕГЭ</SelectItem>
                  <SelectItem value="topic">Тема</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Сложность</Label>
              <Select value={String(form.level)} onValueChange={(v) => update("level", Number(v))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Макс. балл</Label>
              <Select value={String(form.full_mark)} onValueChange={(v) => update("full_mark", Number(v))}>
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
            <Label>Теги (по одному на строку)</Label>
            <Textarea
              value={form.tags_list}
              onChange={(e) => update("tags_list", e.target.value)}
              placeholder={"тег1\nтег2\nтег3"}
              rows={4}
              className="font-mono text-sm"
            />
          </div>

          <div className="flex flex-wrap gap-6">
            <div className="flex items-center gap-2">
              <Switch
                checked={form.is_rotate}
                onCheckedChange={(v) => update("is_rotate", v)}
              />
              <Label>Вращение ответа</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={form.is_selfcheck}
                onCheckedChange={(v) => update("is_selfcheck", v)}
              />
              <Label>Самопроверка</Label>
            </div>
          </div>

          <Button className="w-full sm:w-auto" onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Сохранение..." : "Сохранить вопрос"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
