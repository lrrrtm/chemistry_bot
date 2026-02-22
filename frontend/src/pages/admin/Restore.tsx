import { useState, useRef } from "react";
import { UploadCloud, AlertTriangle, CheckCircle2, FileArchive, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function RestorePage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (f: File | null) => {
    setFile(f);
    setConfirmed(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFileChange(f);
  };

  const handleRestore = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const res = await api.restoreBackup(file);
      toast.success(res.message || "Резервная копия восстановлена");
      setFile(null);
      setConfirmed(false);
    } catch (e: any) {
      toast.error(e.message || "Ошибка при восстановлении");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)]">
          Восстановление из резервной копии
        </h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Загрузите zip-архив с файлом .sql и папкой images/
        </p>
      </div>

      {/* Warning */}
      <div className="flex gap-3 p-4 rounded-lg border border-yellow-400/40 bg-yellow-400/10 text-yellow-700 dark:text-yellow-300">
        <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium">Внимание: операция необратима</p>
          <p className="mt-0.5 opacity-80">
            Текущие данные базы данных и изображения будут перезаписаны данными из архива.
          </p>
        </div>
      </div>

      {/* Drop zone */}
      <div
        className="border-2 border-dashed border-[var(--color-border)] rounded-lg p-8 text-center cursor-pointer hover:border-[var(--color-primary)] transition-colors"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".zip"
          className="hidden"
          onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileArchive className="h-8 w-8 text-[var(--color-primary)]" />
            <div className="text-left">
              <p className="font-medium text-[var(--color-foreground)] text-sm">{file.name}</p>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                {(file.size / 1024 / 1024).toFixed(2)} МБ
              </p>
            </div>
            <button
              className="ml-2 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
              onClick={(e) => {
                e.stopPropagation();
                handleFileChange(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <UploadCloud className="h-10 w-10 mx-auto text-[var(--color-muted-foreground)]" />
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Перетащите .zip-архив или нажмите для выбора
            </p>
          </div>
        )}
      </div>

      {/* Confirmation checkbox */}
      {file && (
        <label className="flex items-start gap-3 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="mt-0.5 h-4 w-4 accent-[var(--color-primary)]"
          />
          <span className="text-sm text-[var(--color-foreground)]">
            Я понимаю, что текущие данные будут безвозвратно перезаписаны
          </span>
        </label>
      )}

      {/* Action button */}
      <Button
        disabled={!file || !confirmed || loading}
        onClick={handleRestore}
        className="w-full"
        variant="destructive"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            Восстановление...
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Восстановить из резервной копии
          </span>
        )}
      </Button>

      {/* Format hint */}
      <div className="text-xs text-[var(--color-muted-foreground)] space-y-1">
        <p className="font-medium">Ожидаемая структура архива:</p>
        <pre className="font-mono bg-[var(--color-accent)] rounded p-2">{`backup.zip
├── backup.sql
└── images/
    ├── answers/
    ├── questions/
    └── users/`}</pre>
      </div>
    </div>
  );
}
