import { forwardRef, type ComponentPropsWithoutRef } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const SearchInput = forwardRef<
  HTMLInputElement,
  ComponentPropsWithoutRef<typeof Input> & { wrapperClassName?: string }
>(({ wrapperClassName, className, ...props }, ref) => (
  <div className={cn("relative", wrapperClassName)}>
    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--color-muted-foreground)]" />
    <Input ref={ref} className={cn("pl-8", className)} {...props} />
  </div>
));

SearchInput.displayName = "SearchInput";
