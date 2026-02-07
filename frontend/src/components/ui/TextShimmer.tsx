import React from "react";
import { cn } from "../../lib/utils";

export const TextShimmer = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <p
      className={cn(
        "inline-flex animate-shimmer items-center justify-center bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%] bg-clip-text text-transparent",
        className
      )}
    >
      {children}
    </p>
  );
};
