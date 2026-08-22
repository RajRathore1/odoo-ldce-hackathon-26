import { cn } from "@/lib/cn";

type Variant = "primary" | "accent" | "outline" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-xl font-medium whitespace-nowrap transition-all active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-60 disabled:active:scale-100";

const variants: Record<Variant, string> = {
  primary: "bg-primary text-white shadow-sm hover:bg-primary/90 hover:shadow-md",
  accent: "bg-accent text-white shadow-sm hover:bg-accent/90 hover:shadow-md",
  outline: "border border-border bg-surface text-text hover:border-text/30 hover:bg-subtle",
  ghost: "text-text-muted hover:bg-subtle hover:text-text",
  danger: "bg-danger text-white shadow-sm hover:bg-danger/90 hover:shadow-md",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

export function buttonStyles(
  variant: Variant = "primary",
  size: Size = "md",
  className?: string,
) {
  return cn(base, variants[variant], sizes[size], className);
}

type ButtonProps = React.ComponentProps<"button"> & {
  variant?: Variant;
  size?: Size;
};

export function Button({
  variant,
  size,
  className,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={buttonStyles(variant, size, className)}
      {...props}
    />
  );
}
