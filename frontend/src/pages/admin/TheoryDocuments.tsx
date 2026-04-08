import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { ExternalLink, FileText, RefreshCw, Save, Trash2, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { TagHierarchySelector } from "@/components/TagHierarchySelector";
import { SearchInput } from "@/components/ui/SearchInput";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileDropZone } from "@/components/ui/FileDropZone";

type TheoryDocumentItem = {
  id: number;
  title: string;
  tags_list: string[];
  file_size: number;
  mime_type: string;
  created_at: string | null;
};

function formatSize(size: number) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} МБ`;
  if (size >= 1024) return `${(size / 1024).toFixed(1)} КБ`;
  return `${size} Б`;
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ru-RU");
}

function getTitleFromFileName(fileName: string) {
  return fileName.replace(/\.pdf$/i, "").trim();
}

export function TheoryDocuments() {
  const [documents, setDocuments] = useState<TheoryDocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const [title, setTitle] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingTags, setEditingTags] = useState<string[]>([]);
  const [replacementFile, setReplacementFile] = useState<File | null>(null);
  const [updating, setUpdating] = useState(false);
  const [replacingFile, setReplacingFile] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const activeEditingDocument = useMemo(
    () => documents.find((document) => document.id === editingId) ?? null,
    [documents, editingId]
  );

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setLoading(true);
      api
        .getTheoryDocuments(search)
        .then(setDocuments)
        .catch((error) => {
          toast.error(error instanceof Error ? error.message : "Не удалось загрузить документы");
          setDocuments([]);
        })
        .finally(() => setLoading(false));
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [search]);

  const resetCreateForm = () => {
    setTitle("");
    setTags([]);
    setFile(null);
  };

  const handleCreateFileChange = (nextFile: File | null) => {
    setFile(nextFile);
    if (nextFile) {
      setTitle(getTitleFromFileName(nextFile.name));
    }
  };

  const handleCreate = async () => {
    const normalizedTitle = title.trim();
    if (!normalizedTitle) {
      toast.warning("Введите название документа");
      return;
    }
    if (!file) {
      toast.warning("Выберите PDF-файл");
      return;
    }

    setSaving(true);
    try {
      const response = await api.createTheoryDocument({
        title: normalizedTitle,
        tags_list: tags,
        file,
      });
      setDocuments((current) => [response.document, ...current]);
      resetCreateForm();
      toast.success("Документ загружен");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Не удалось загрузить документ");
    } finally {
      setSaving(false);
    }
  };

  const startEditing = (document: TheoryDocumentItem) => {
    setEditingId(document.id);
    setEditingTitle(document.title);
    setEditingTags(document.tags_list);
    setReplacementFile(null);
  };

  const stopEditing = () => {
    setEditingId(null);
    setEditingTitle("");
    setEditingTags([]);
    setReplacementFile(null);
  };

  const handleUpdate = async () => {
    if (!editingId) return;

    const normalizedTitle = editingTitle.trim();
    if (!normalizedTitle) {
      toast.warning("Введите название документа");
      return;
    }

    setUpdating(true);
    try {
      const response = await api.updateTheoryDocument(editingId, {
        title: normalizedTitle,
        tags_list: editingTags,
      });
      setDocuments((current) =>
        current.map((document) => (document.id === editingId ? response.document : document))
      );
      toast.success("Изменения сохранены");
      stopEditing();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Не удалось сохранить документ");
    } finally {
      setUpdating(false);
    }
  };

  const handleReplaceFile = async () => {
    if (!editingId || !replacementFile) return;

    setReplacingFile(true);
    try {
      const response = await api.replaceTheoryDocumentFile(editingId, replacementFile);
      setDocuments((current) =>
        current.map((document) => (document.id === editingId ? response.document : document))
      );
      setReplacementFile(null);
      toast.success("PDF-файл заменён");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Не удалось заменить файл");
    } finally {
      setReplacingFile(false);
    }
  };

  const handleDelete = async (documentId: number) => {
    setDeletingId(documentId);
    try {
      await api.deleteTheoryDocument(documentId);
      setDocuments((current) => current.filter((document) => document.id !== documentId));
      if (editingId === documentId) {
        stopEditing();
      }
      toast.success("Документ удалён");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Не удалось удалить документ");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="w-full max-w-none space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Теория</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Загружайте PDF-документы, задавайте им видимые названия и привязывайте к тегам.
        </p>
      </div>

      <div className="grid gap-6 2xl:grid-cols-[minmax(0,1.55fr)_minmax(460px,0.95fr)] 2xl:items-start">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base">Все документы</CardTitle>
                <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
                  Поиск работает по названию документа и по тегам.
                </p>
              </div>
              <SearchInput
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Название или тег..."
                className="md:w-80"
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Загружаем документы...
              </div>
            ) : documents.length === 0 ? (
              <div className="rounded-lg border border-dashed px-4 py-8 text-sm text-[var(--color-muted-foreground)]">
                По вашему запросу ничего не найдено
              </div>
            ) : (
              documents.map((document) => {
                const isEditing = document.id === editingId;
                const visibleTags = document.tags_list.slice(0, 3);
                const hiddenTagsCount = Math.max(0, document.tags_list.length - visibleTags.length);

                return (
                  <div key={document.id} className="space-y-4 rounded-xl border bg-[var(--color-card)] p-4">
                    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px] lg:items-start">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 shrink-0 text-[var(--color-primary)]" />
                          <p className="break-words font-medium">{document.title}</p>
                        </div>

                        <div className="mt-2 flex flex-wrap gap-2">
                          {document.tags_list.length === 0 ? (
                            <Badge variant="outline" className="text-xs">
                              Без тегов
                            </Badge>
                          ) : (
                            <>
                              {visibleTags.map((tag) => (
                                <Badge key={`${document.id}-${tag}`} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                              {hiddenTagsCount > 0 ? (
                                <Badge variant="outline" className="text-xs">
                                  +{hiddenTagsCount}
                                </Badge>
                              ) : null}
                            </>
                          )}
                        </div>

                        <p className="mt-3 text-xs text-[var(--color-muted-foreground)]">
                          {formatSize(document.file_size)} • {formatDate(document.created_at)}
                        </p>
                      </div>

                      <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
                        <Button
                          variant="outline"
                          size="sm"
                          className="justify-center lg:w-full"
                          onClick={() => window.open(api.theoryDocumentUrl(document.id), "_blank", "noopener,noreferrer")}
                        >
                          <ExternalLink className="mr-1.5 h-4 w-4" />
                          Открыть PDF
                        </Button>
                        {isEditing ? (
                          <Button variant="ghost" size="sm" className="justify-center lg:w-full" onClick={stopEditing}>
                            Отмена
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            className="justify-center lg:w-full"
                            onClick={() => startEditing(document)}
                          >
                            Редактировать
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          className="justify-center text-red-600 hover:text-red-700 lg:w-full"
                          onClick={() => handleDelete(document.id)}
                          disabled={deletingId === document.id}
                        >
                          <Trash2 className="mr-1.5 h-4 w-4" />
                          {deletingId === document.id ? "Удаление..." : "Удалить"}
                        </Button>
                      </div>
                    </div>

                    {isEditing && activeEditingDocument ? (
                      <div className="grid gap-4 border-t pt-4">
                        <div className="space-y-2">
                          <Label htmlFor={`title-${document.id}`}>Название</Label>
                          <Input
                            id={`title-${document.id}`}
                            value={editingTitle}
                            onChange={(event) => setEditingTitle(event.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>Теги</Label>
                          <TagHierarchySelector value={editingTags} onChange={setEditingTags} />
                        </div>

                        <div className="space-y-2">
                          <Label>Заменить PDF</Label>
                          <FileDropZone
                            file={replacementFile}
                            onChange={setReplacementFile}
                            accept=".pdf,application/pdf"
                            compact
                            hint="При необходимости загрузите новый PDF"
                          />
                          <div className="flex flex-wrap gap-2">
                            <Button onClick={handleUpdate} disabled={updating}>
                              <Save className="mr-1.5 h-4 w-4" />
                              {updating ? "Сохранение..." : "Сохранить"}
                            </Button>
                            <Button
                              variant="outline"
                              onClick={handleReplaceFile}
                              disabled={!replacementFile || replacingFile}
                            >
                              <Upload className="mr-1.5 h-4 w-4" />
                              {replacingFile ? "Замена..." : "Заменить PDF"}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card className="2xl:sticky 2xl:top-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Новый документ</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theory-title">Видимое название</Label>
              <Input
                id="theory-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Например, Окислительно-восстановительные реакции"
              />
            </div>

            <div className="space-y-2">
              <Label>Теги</Label>
              <TagHierarchySelector value={tags} onChange={setTags} />
            </div>

            <div className="space-y-2">
              <Label>PDF-файл</Label>
              <FileDropZone
                file={file}
                onChange={handleCreateFileChange}
                accept=".pdf,application/pdf"
                compact
                hint="Перетащите PDF или нажмите для выбора"
              />
            </div>

            <Button onClick={handleCreate} disabled={saving} className="w-full">
              <Upload className="mr-2 h-4 w-4" />
              {saving ? "Загрузка..." : "Загрузить документ"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
