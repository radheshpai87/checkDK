import React from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

export const BackgroundGradient = ({
  children,
  className,
  containerClassName,
}: {
  children?: React.ReactNode;
  className?: string;
  containerClassName?: string;
}) => {
  return (
    <div className={cn("relative p-[1px] group h-full", containerClassName)}>
      <motion.div
        className={cn(
          "absolute inset-0 rounded-2xl opacity-40 group-hover:opacity-90 blur-xl transition-all duration-500",
          "bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.55),transparent_60%)]"
        )}
        whileHover={{ scale: 1.02 }}
      />
      <div
        className={cn(
          "relative bg-slate-900/80 border border-slate-800 group-hover:border-slate-700 rounded-2xl p-6 h-full backdrop-blur-sm transition-all duration-300",
          className
        )}
      >
        {children}
      </div>
    </div>
  );
};
