import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Save, Calculator } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type EgeRow = { id: number; input_mark: number; output_mark: number };

export function EgeConverting() {
  const [data, setData] = useState<EgeRow[]>([]);
  const [edited, setEdited] = useState<Record<number, number>>({});
  const [errors, setErrors] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getEgeConverting()
      .then((rows) => {
        setData(rows);
        setEdited(Object.fromEntries(rows.map((r) => [r.input_mark, r.output_mark])));
      })
      .catch(() => toast.error("Ошибка загрузки данных"))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (inputMark: number, value: string) => {
    const num = Number(value);
    if (value === "" || isNaN(num) || num < 1 || num > 100) {
      setErrors((prev) => new Set(prev).add(inputMark));
    } else {
      setErrors((prev) => {
        const next = new Set(prev);
        next.delete(inputMark);
        return next;
      });
      setEdited((prev) => ({ ...prev, [inputMark]: num }));
    }
  };

  const handleSave = async () => {
    if (errors.size > 0) {
      toast.warning("Исправьте ошибки перед сохранением");
      return;
    }
    setSaving(true);
    try {
      await api.updateEgeConverting(
        Object.fromEntries(Object.entries(edited).map(([k, v]) => [k, v]))
      );
      toast.success("Таблица баллов обновлена");
    } catch {
      toast.error("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-[var(--color-muted-foreground)]">Загрузка...</div>;

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Конвертация баллов ЕГЭ</h1>
          <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
            Таблица перевода первичных баллов во вторичные
          </p>
        </div>
        <Button onClick={handleSave} disabled={saving || errors.size > 0}>
          <Save className="h-4 w-4 mr-2" />
          {saving ? "Сохранение..." : "Сохранить"}
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Таблица баллов
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-[var(--color-muted)]">
                  <th className="text-left px-4 py-2.5 font-medium text-[var(--color-muted-foreground)]">
                    Первичный
                  </th>
                  <th className="text-left px-4 py-2.5 font-medium text-[var(--color-muted-foreground)]">
                    Вторичный
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => {
                  const hasError = errors.has(row.input_mark);
                  return (
                    <tr key={row.id} className="border-b last:border-0 hover:bg-[var(--color-muted)] transition-colors">
                      <td className="px-4 py-2 font-medium">{row.input_mark}</td>
                      <td className="px-4 py-2">
                        <Input
                          type="number"
                          min={1}
                          max={100}
                          defaultValue={edited[row.input_mark] ?? row.output_mark}
                          onChange={(e) => handleChange(row.input_mark, e.target.value)}
                          className={`h-8 w-24 text-sm ${hasError ? "border-red-500 focus-visible:ring-red-500" : ""}`}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {errors.size > 0 && (
        <p className="text-sm text-[var(--color-destructive)]">
          Исправьте {errors.size} ошибки: значения должны быть от 1 до 100
        </p>
      )}
    </div>
  );
}
