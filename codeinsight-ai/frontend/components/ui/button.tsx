import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "outline" | "ghost" | "subtle";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantStyles: Record<Variant, string> = {
  default:
    "bg-primary text-primary-foreground hover:opacity-90 shadow-lg shadow-primary/20",
  outline: "border border-border bg-transparent hover:bg-muted text-foreground",
  ghost: "bg-transparent hover:bg-muted text-foreground",
  subtle: "bg-muted text-foreground hover:bg-muted/70",
};

const sizeStyles: Record<Size, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
