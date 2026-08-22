import { cn } from "@/lib/cn";

type Size = "sm" | "md" | "lg" | "xl";

const sizes: Record<Size, string> = {
  sm: "size-8 text-xs",
  md: "size-10 text-sm",
  lg: "size-14 text-base",
  xl: "size-24 text-2xl",
};

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? "")
    .join("")
    .toUpperCase();
}

type AvatarProps = {
  name: string;
  src?: string | null;
  size?: Size;
  className?: string;
};

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  return (
    <span
      role="img"
      aria-label={name}
      style={src ? { backgroundImage: `url(${src})` } : undefined}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-primary/10 bg-cover bg-center font-semibold text-primary select-none",
        sizes[size],
        className,
      )}
    >
      {!src && initials(name)}
    </span>
  );
}
