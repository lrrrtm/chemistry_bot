import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  text: string;
  animate?: boolean;
  className?: string;
}

export function EmptyState({ icon: Icon, text, animate, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-[var(--color-muted-foreground)]", className)}>
      {Icon && <Icon className={cn("h-8 w-8 mb-2 opacity-30", animate && "animate-pulse")} />}
      <p className="text-xs">{text}</p>
    </div>
  );
}
