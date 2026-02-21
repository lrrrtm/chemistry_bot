import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Search, ChevronRight, Users } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

type User = { id: number; telegram_id: number; name: string };

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function Students() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.getUsers()
      .then(setUsers)
      .catch(() => toast.error("Ошибка загрузки учеников"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    String(u.telegram_id).includes(search)
  );

  if (loading) {
    return <div className="text-center text-[var(--color-muted-foreground)] py-12">Загрузка...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ученики</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">
          {users.length} {users.length === 1 ? "ученик" : "учеников"} зарегистрировано
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-muted-foreground)]" />
        <Input
          placeholder="Поиск по имени или Telegram ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-[var(--color-muted-foreground)]">
          <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>{search ? "Ученики не найдены" : "Нет учеников"}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((user) => (
            <Card
              key={user.telegram_id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/admin/students/${user.telegram_id}`)}
            >
              <CardContent className="flex items-center gap-3 py-3 px-4">
                <Avatar className="h-10 w-10 shrink-0">
                  <AvatarImage
                    src={api.imageUrl.user(user.telegram_id)}
                    alt={user.name}
                  />
                  <AvatarFallback className="text-xs font-semibold">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{user.name}</p>
                  <p className="text-xs text-[var(--color-muted-foreground)]">id{user.telegram_id}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-[var(--color-muted-foreground)] shrink-0" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
