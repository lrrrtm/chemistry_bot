import { useState, useRef, useEffect } from "react";
import { UploadCloud, AlertTriangle, CheckCircle2, FileArchive, X, Clock, Send } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

const PHASE_LABELS: Record<Phase, string> = {
  idle:       "",
  uploading:  "Загрузка файла",
  processing: "Восстановление базы данных",
  done:       "Готово",
  error:      "Ошибка",
};

// MSK = UTC+3
function utcToMsk(utc: string): string {
  if (!utc || !utc.includes(":")) return utc;
  const [h, m] = utc.split(":").map(Number);
  const msk = (h + 3) % 24;
  return `${String(msk).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function mskToUtc(msk: string): string {
  if (!msk || !msk.includes(":")) return msk;
  const [h, m] = msk.split(":").map(Number);
  const utc = (h - 3 + 24) % 24;
  return `${String(utc).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function RestorePage() {
  // ── Restore state ──────────────────────────────────────────────────────────
  const [file, setFile]           = useState<File | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [phase, setPhase]         = useState<Phase>("idle");
  const [progress, setProgress]   = useState(0);
  const inputRef  = useRef<HTMLInputElement>(null);
  const crawlRef  = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Backup settings state ──────────────────────────────────────────────────
  const [backupTime,       setBackupTime]       = useState("");
  const [backupChatId,     setBackupChatId]     = useState("");
  const [settingsSaving,   setSettingsSaving]   = useState(false);
  const [backupNowLoading, setBackupNowLoading] = useState(false);

  useEffect(() => {
    api.getBackupSettings()
      .then((s) => { setBackupTime(utcToMsk(s.time)); setBackupChatId(s.chat_id); })
      .catch(() => {});
  }, []);

  const handleSaveSettings = async () => {
    setSettingsSaving(true);
    try {
      await api.saveBackupSettings({ time: mskToUtc(backupTime), chat_id: backupChatId });
      toast.success("Настройки сохранены");
    } catch (e: any) {
      toast.error(e.message || "Ошибка сохранения");
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleBackupNow = async () => {
    setBackupNowLoading(true);
    try {
      const res = await api.runBackupNow();
      toast.success(res.message || "Резервная копия отправлена");
    } catch (e: any) {
      toast.error(e.message || "Ошибка создания резервной копии");
    } finally {
      setBackupNowLoading(false);
    }
  };

  // ── Restore logic ──────────────────────────────────────────────────────────
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

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 60));
    };

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

      {/* ── Restore section ────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)]">
          Восстановление из резервной копии
        </h1>
        <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
          Загрузите zip-архив с файлом .sql и папкой images/
        </p>
      </div>

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
        <Button disabled={!file || !confirmed} onClick={handleRestore} className="w-full" variant="destructive">
          <CheckCircle2 className="h-4 w-4 mr-2" />
          {phase === "error" ? "Попробовать снова" : "Восстановить из резервной копии"}
        </Button>
      )}

      <div className="text-xs text-[var(--color-muted-foreground)] space-y-1">
        <p className="font-medium">Ожидаемая структура архива:</p>
        <pre className="font-mono bg-[var(--color-accent)] rounded p-2">{`backup.zip
├── backup.sql
└── images/
    ├── answers/
    ├── questions/
    └── users/`}</pre>
      </div>

      {/* ── Backup settings section ────────────────────────────────────────── */}
      <div className="border-t border-[var(--color-border)] pt-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-foreground)]">
            Автоматические резервные копии
          </h2>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-0.5">
            Ежедневная отправка архива с БД и изображениями в Telegram
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="backup-time" className="flex items-center gap-1.5 text-sm">
              <Clock className="h-3.5 w-3.5" />
              Время (МСК)
            </Label>
            <Input
              id="backup-time"
              type="time"
              value={backupTime}
              onChange={(e) => setBackupTime(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="backup-chat" className="flex items-center gap-1.5 text-sm">
              <Send className="h-3.5 w-3.5" />
              Chat ID в Telegram
            </Label>
            <Input
              id="backup-chat"
              type="text"
              value={backupChatId}
              onChange={(e) => setBackupChatId(e.target.value)}
              placeholder="-1001234567890"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <Button onClick={handleSaveSettings} disabled={settingsSaving} className="flex-1">
            {settingsSaving ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Сохранение...
              </span>
            ) : "Сохранить расписание"}
          </Button>

          <Button
            variant="outline"
            onClick={handleBackupNow}
            disabled={backupNowLoading || !backupChatId.trim()}
            className="flex-1"
          >
            {backupNowLoading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                Создание...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Send className="h-4 w-4" />
                Создать сейчас
              </span>
            )}
          </Button>
        </div>

        <p className="text-xs text-[var(--color-muted-foreground)]">
          Убедитесь, что бот добавлен в чат и имеет права на отправку файлов.
          Chat ID группы можно узнать, переслав сообщение из группы боту <code>@userinfobot</code>.
        </p>
      </div>
    </div>
  );
}
