import { useRef, useState } from "react";
import { toast } from "sonner";
import { Download, Upload, FileSpreadsheet } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function Topics() {
  const [downloading, setDownloading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await api.exportTopicsExcel();
      downloadBlob(blob, "chembot_topics_list.xlsx");
      toast.success("Файл скачан");
    } catch {
      toast.error("Ошибка при скачивании");
    } finally {
      setDownloading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.warning("Выберите файл");
      return;
    }
    setUploading(true);
    try {
      const result = await api.importTopicsExcel(file);
      toast.success(result.message);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка импорта");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Темы и теги</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
          Управление темами и тегами через Excel-файл
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Download className="h-4 w-4" />
            Скачать текущие темы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[var(--color-muted-foreground)] mb-4">
            Скачайте файл с текущим списком тем и тегов, отредактируйте его и загрузите обратно.
          </p>
          <Button onClick={handleDownload} disabled={downloading} variant="outline">
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            {downloading ? "Скачивание..." : "Скачать Excel"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Загрузить обновлённый файл
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-[var(--color-muted-foreground)]">
            Загрузите отредактированный Excel-файл для обновления тем и тегов в базе данных.
          </p>
          <div className="space-y-2">
            <Label htmlFor="topics-file">Файл (.xlsx)</Label>
            <Input
              id="topics-file"
              ref={fileRef}
              type="file"
              accept=".xlsx"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <Button onClick={handleUpload} disabled={uploading || !file}>
            <Upload className="h-4 w-4 mr-2" />
            {uploading ? "Загрузка..." : "Загрузить"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
