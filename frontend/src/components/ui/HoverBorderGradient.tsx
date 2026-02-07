import React from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

export const HoverBorderGradient = ({
  children,
  containerClassName,
  className,
  as: Tag = "button",
  duration = 1,
  ...props
}: React.PropsWithChildren<
  {
    as?: React.ElementType;
    containerClassName?: string;
    className?: string;
    duration?: number;
  } & React.HTMLAttributes<HTMLElement>
>) => {
  return (
    <Tag
      className={cn(
        "relative inline-flex overflow-hidden rounded-xl p-[1px]",
        containerClassName
      )}
      {...props}
    >
      <motion.span
        className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#6366f1_0%,#8b5cf6_50%,#6366f1_100%)]"
        style={{
          animation: `spin ${duration}s linear infinite`,
        }}
      />
      <span
        className={cn(
          "inline-flex h-full w-full cursor-pointer items-center justify-center rounded-xl bg-slate-900/90 px-6 py-3 text-sm font-medium text-white backdrop-blur-3xl transition-colors hover:bg-slate-800",
          className
        )}
      >
        {children}
      </span>
    </Tag>
  );
};
