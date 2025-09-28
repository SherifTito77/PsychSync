// // // // // src/components/Button.tsx

// src/components/Button.tsx
import React from 'react';
import { ButtonProps } from '../types/components';

const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  className = '', 
  disabled = false, 
  variant = 'primary',
  type = 'button',
  ...props 
}) => {
  const baseStyles = 'px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantStyles = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;

// import React from "react";
// import { ButtonProps } from "../types/components";

// const Button: React.FC<ButtonProps> = ({
//   children,
//   onClick,
//   className = "",
//   disabled = false,
//   variant = "primary",
//   ...props
// }) => {
//   const baseStyles =
//     "px-4 py-2 rounded font-medium focus:outline-none transition duration-200";

//   const variants: Record<string, string> = {
//     primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400",
//     secondary:
//       "bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:bg-gray-100",
//     danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400",
//   };

//   return (
//     <button
//       onClick={onClick}
//       disabled={disabled}
//       className={`${baseStyles} ${variants[variant]} ${className}`}
//       {...props}
//     >
//       {children}
//     </button>
//   );
// };

// export default Button;

// // // src/components/Button.tsx
// // import React from "react";
// // import { ButtonProps } from "../types/components";

// // const Button: React.FC<ButtonProps> = ({
// //   children,
// //   onClick,
// //   className = "",
// //   disabled = false,
// //   variant = "primary",
// //   ...props
// // }) => {
// //   const baseStyles =
// //     "px-4 py-2 rounded font-medium focus:outline-none transition duration-200";

// //   const variants: Record<string, string> = {
// //     primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400",
// //     secondary:
// //       "bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:bg-gray-100",
// //     danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400",
// //   };

// //   return (
// //     <button
// //       onClick={onClick}
// //       disabled={disabled}
// //       className={`${baseStyles} ${variants[variant]} ${className}`}
// //       {...props}
// //     >
// //       {children}
// //     </button>
// //   );
// // };

// // export default Button;

// // // // src/components/Button.tsx
// // // import React from "react";
// // // import { ButtonProps } from "../types/components";

// // // const Button: React.FC<ButtonProps> = ({ children, ...props }) => {

// // // export const Button: React.FC<ButtonProps> = ({
// // //   children,
// // //   onClick,
// // //   className = "",
// // //   disabled = false,
// // //   variant = "primary",
// // //   ...props
// // // }) => {
// // //   const baseStyles =
// // //     "px-4 py-2 rounded font-medium focus:outline-none transition duration-200";
// // //   const variants: Record<string, string> = {
// // //     primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400",
// // //     secondary:
// // //       "bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:bg-gray-100",
// // //     danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400",
// // //   };

// // //   return (
// // //     <button
// // //       onClick={onClick}
// // //       className={`${baseStyles} ${variants[variant]} ${className}`}
// // //       disabled={disabled}
// // //       {...props}
// // //     >
// // //       {children}
// // //     </button>
// // //   );
// // // };

// // // };

// // // export default Button;

// // // // export default Button; // ✅ now App.tsx can use `import Button`

// // // // import React from "react";
// // // // import { ButtonProps } from "../types/components";

// // // // export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

// // // // const Button: React.FC<ButtonProps> = ({ children, ...props }) => (
// // // //   <button {...props}>{children}</button>
// // // // );

// // // // export const Button: React.FC<ButtonProps> = ({
// // // //   children,
// // // //   onClick,
// // // //   className,
// // // //   disabled,
// // // //   variant,
// // // //   ...props
// // // // }) => {
// // // //   return (
// // // //     <button
// // // //       onClick={onClick}
// // // //       disabled={disabled}
// // // //       className={`btn ${variant || ""} ${className || ""}`}
// // // //       {...props}
// // // //     >
// // // //       {children}
// // // //     </button>
// // // //   );
// // // // };
// // // // export default Button; // ✅ now App.tsx can use `import Button`

// // // // // import React from 'react';
// // // // // import { ButtonProps } from '../types/components';

// // // // // export const Button: React.FC<ButtonProps> = ({
// // // // //   children,
// // // // //   onClick,
// // // // //   className = '',
// // // // //   disabled = false,
// // // // //   variant = 'primary',
// // // // //   ...props
// // // // // }) => {
// // // // //   // Component implementation with proper typing
// // // // // };
