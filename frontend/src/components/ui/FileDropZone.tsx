import { useRef } from "react";
import { UploadCloud, FileArchive, X, Upload } from "lucide-react";

type FileDropZoneProps = {
  file: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
  disabled?: boolean;
  hint?: string;
  compact?: boolean;
  /** When set, show an image preview instead of file name/size */
  previewUrl?: string | null;
};

export function FileDropZone({
  file,
  onChange,
  accept = "*",
  disabled = false,
  hint = "Перетащите файл или нажмите для выбора",
  compact = false,
  previewUrl,
}: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const isImage = previewUrl !== undefined;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      const f = e.dataTransfer.files[0];
      if (f) {
        // If accept filter is set, do a basic check
        if (accept !== "*") {
          const exts = accept.split(",").map((s) => s.trim().toLowerCase());
          const matchesExt = exts.some((ext) =>
            ext.startsWith(".") ? f.name.toLowerCase().endsWith(ext) : f.type === ext
          );
          if (!matchesExt) return;
        }
        onChange(f);
      }
    }
  };

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="space-y-2">
      {/* Image preview (when in image mode) */}
      {isImage && previewUrl && (
        <div className="relative rounded-lg overflow-hidden border">
          <img src={previewUrl} alt="preview" className="w-full max-h-40 object-contain" />
          <button
            className="absolute top-1.5 right-1.5 bg-black/60 text-white rounded-full p-0.5 hover:bg-black/80"
            onClick={clear}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div
        className={`border-2 border-dashed rounded-lg text-center transition-colors ${
          compact ? "p-4" : "p-8"
        } ${
          disabled
            ? "opacity-50 pointer-events-none border-[var(--color-border)]"
            : "cursor-pointer hover:border-[var(--color-primary)] border-[var(--color-border)]"
        }`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => onChange(e.target.files?.[0] ?? null)}
        />
        {!isImage && file ? (
          <div className="flex items-center justify-center gap-3">
            <FileArchive className={`${compact ? "h-6 w-6" : "h-8 w-8"} text-[var(--color-primary)]`} />
            <div className="text-left">
              <p className="font-medium text-[var(--color-foreground)] text-sm">{file.name}</p>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                {(file.size / 1024 / 1024).toFixed(2)} МБ
              </p>
            </div>
            {!disabled && (
              <button
                className="ml-2 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
                onClick={clear}
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            {isImage ? (
              <Upload className={`${compact ? "h-5 w-5" : "h-6 w-6"} mx-auto text-[var(--color-muted-foreground)]`} />
            ) : (
              <UploadCloud className={`${compact ? "h-8 w-8" : "h-10 w-10"} mx-auto text-[var(--color-muted-foreground)]`} />
            )}
            <p className={`${isImage ? "text-xs" : "text-sm"} text-[var(--color-muted-foreground)]`}>{hint}</p>
          </div>
        )}
      </div>
    </div>
  );
}
