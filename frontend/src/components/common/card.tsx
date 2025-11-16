import React from "react";
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <div
    className={`bg-white rounded-xl border border-gray-200 p-4 shadow-sm ${className}`}
    {...props}
  >
    {children}
  </div>
);
