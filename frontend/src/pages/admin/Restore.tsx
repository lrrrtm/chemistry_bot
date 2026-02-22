import { useState, useRef, useEffect } from "react";
import { UploadCloud, AlertTriangle, CheckCircle2, FileArchive, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

const PHASE_LABELS: Record<Phase, string> = {
  idle:       "",
  uploading:  "Загрузка файла",
  processing: "Восстановление базы данных",
  done:       "Готово",
  error:      "Ошибка",
};

export function RestorePage() {
  const [file, setFile]           = useState<File | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [phase, setPhase]         = useState<Phase>("idle");
  const [progress, setProgress]   = useState(0);
  const inputRef  = useRef<HTMLInputElement>(null);
  const crawlRef  = useRef<ReturnType<typeof setInterval> | null>(null);

  const loading = phase === "uploading" || phase === "processing";

  const stopCrawl = () => {
    if (crawlRef.current) { clearInterval(crawlRef.current); crawlRef.current = null; }
  };

  useEffect(() => () => stopCrawl(), []);

  const handleFileChange = (f: File | null) => {
    setFile(f);
    setConfirmed(false);
    setPhase("idle");
    setProgress(0);
    stopCrawl();
  };

  const handleRestore = () => {
    if (!file) return;

    const token = localStorage.getItem("admin_token");
    const xhr   = new XMLHttpRequest();
    const form  = new FormData();
    form.append("file", file);

    setPhase("uploading");
    setProgress(0);

    // 0–60 % — реальный прогресс загрузки файла
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 60));
    };

    // файл отправлен → ползём к 95 % пока сервер обрабатывает
    xhr.upload.onload = () => {
      setPhase("processing");
      setProgress(62);
      stopCrawl();
      crawlRef.current = setInterval(() => {
        setProgress((p) => {
          if (p >= 94) { stopCrawl(); return 94; }
          return p + 1;
        });
      }, 350);
    };

    xhr.onload = () => {
      stopCrawl();
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(100);
        setPhase("done");
        setTimeout(() => { setPhase("idle"); setProgress(0); }, 3000);
        try { toast.success(JSON.parse(xhr.responseText).message || "Восстановлено"); }
        catch { toast.success("Восстановлено"); }
        setFile(null);
        setConfirmed(false);
        if (inputRef.current) inputRef.current.value = "";
      } else {
        setPhase("error");
        try { toast.error(JSON.parse(xhr.responseText).detail || "Ошибка"); }
        catch { toast.error("Ошибка при восстановлении"); }
      }
    };

    xhr.onerror = () => { stopCrawl(); setPhase("error"); toast.error("Ошибка сети"); };

    xhr.open("POST", "/api/admin/restore");
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.send(form);
  };

  const barColor =
    phase === "error" ? "bg-red-500" :
    phase === "done"  ? "bg-green-500" :
    "bg-[var(--color-primary)]";

  const labelColor =
    phase === "error" ? "text-red-500" :
    phase === "done"  ? "text-green-600 dark:text-green-400" :
    "text-[var(--color-foreground)]";

  const phaseSubtext: Partial<Record<Phase, string>> = {
    uploading:  "Передача файла на сервер...",
    processing: "Импорт базы данных и изображений, может занять некоторое время...",
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
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          loading
            ? "opacity-50 pointer-events-none border-[var(--color-border)]"
            : "cursor-pointer hover:border-[var(--color-primary)] border-[var(--color-border)]"
        }`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); if (!loading) handleFileChange(e.dataTransfer.files[0] ?? null); }}
        onClick={() => !loading && inputRef.current?.click()}
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
            {!loading && (
              <button
                className="ml-2 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
                onClick={(e) => { e.stopPropagation(); handleFileChange(null); if (inputRef.current) inputRef.current.value = ""; }}
              >
                <X className="h-4 w-4" />
              </button>
            )}
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

      {/* Progress bar */}
      {phase !== "idle" && (
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-sm">
            <span className={`font-medium ${labelColor}`}>{PHASE_LABELS[phase]}</span>
            <span className="text-[var(--color-muted-foreground)] tabular-nums">{progress}%</span>
          </div>
          <div className="h-3 rounded-full bg-[var(--color-accent)] overflow-hidden">
            <div
              className={`h-full rounded-full transition-[width] duration-300 ${barColor}`}
              style={{ width: `${progress}%` }}
            />
          </div>
          {phaseSubtext[phase] && (
            <p className="text-xs text-[var(--color-muted-foreground)]">{phaseSubtext[phase]}</p>
          )}
        </div>
      )}

      {/* Confirmation + button (only when not in progress) */}
      {(phase === "idle" || phase === "error") && file && (
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

      {(phase === "idle" || phase === "error") && (
        <Button
          disabled={!file || !confirmed}
          onClick={handleRestore}
          className="w-full"
          variant="destructive"
        >
          <CheckCircle2 className="h-4 w-4 mr-2" />
          {phase === "error" ? "Попробовать снова" : "Восстановить из резервной копии"}
        </Button>
      )}

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
