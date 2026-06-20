"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const button = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[12px] text-sm font-medium transition-all duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)] outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-2 focus-visible:ring-offset-ink disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // primary: emerald fill with a soft glow that intensifies on hover
        primary:
          "bg-brand text-on-brand font-semibold shadow-[0_8px_24px_-10px_rgba(14,159,110,0.55)] hover:shadow-[0_12px_30px_-8px_rgba(14,159,110,0.7)] hover:brightness-[1.05]",
        // secondary: glass
        secondary:
          "glass text-fg hover:ring-glow hover:text-brand",
        ghost: "text-fg-muted hover:text-fg hover:bg-hover",
        outline:
          "border border-line-strong text-fg hover:border-brand/50 hover:text-brand",
        danger:
          "bg-negative/15 text-negative border border-negative/30 hover:bg-negative/25",
        link: "text-brand underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        sm: "h-9 px-3.5",
        md: "h-11 px-5",
        lg: "h-12 px-6 text-[0.95rem]",
        icon: "h-10 w-10 p-0",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(button({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
