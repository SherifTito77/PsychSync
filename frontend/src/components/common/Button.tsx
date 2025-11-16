// File: ../components/common/Button.tsx
import React from 'react';
import LoadingSpinner from './LoadingSpinner';
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'default' | 'outline' | 'ghost' | 'link';
  size?: 'small' | 'medium' | 'large' | 'sm';
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}
const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled,
  className = '',
  icon,
  children,
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  const variantClasses: Record<string, string> = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    default: 'bg-white text-black border border-gray-300 hover:bg-gray-100 focus:ring-gray-400',
    outline: 'bg-transparent border border-gray-500 text-gray-700 hover:bg-gray-50 focus:ring-gray-400',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-400',
    link: 'bg-transparent text-blue-600 hover:text-blue-800 underline hover:no-underline',
  };
  const sizeClasses: Record<string, string> = {
    small: 'px-3 py-2 text-sm',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base',
    sm: 'px-2 py-1 text-xs',
  };
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  return (
    <button className={classes} disabled={disabled || loading} {...props}>
      {loading && (
        <span className="mr-2">
          <LoadingSpinner size="small" color={variant === 'secondary' || variant === 'outline' ? 'black' : 'white'} />
        </span>
      )}
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};
export { Button };
export default Button;
export type { ButtonProps };
//  // ../components/common/Button.tsx
// // File: ../components/common/Button.tsx
// import React from 'react';
// import LoadingSpinner from './LoadingSpinner';
// interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
//   variant?: 'primary' | 'secondary' | 'danger';
//   size?: 'small' | 'medium' | 'large';
//   loading?: boolean;
//   children?: React.ReactNode;
// }
// const variantClasses = {
//   primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
//   secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
//   danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
//   default: 'bg-white text-black border border-gray-300 hover:bg-gray-100 focus:ring-gray-400',
//   outline: 'bg-transparent border border-gray-500 text-gray-700 hover:bg-gray-50 focus:ring-gray-400',
// };
// const Button: React.FC<ButtonProps> = ({
//   variant = 'primary',
//   size = 'medium',
//   loading = false,
//   disabled,
//   className = '',
//   children,
//   ...props
// }) => {
//   const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
//   const variantClasses = {
//     primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
//     secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
//     danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
//   };
//   const sizeClasses = {
//     small: 'px-3 py-2 text-sm',
//     medium: 'px-4 py-2 text-sm',
//     large: 'px-6 py-3 text-base',
//   };
//   const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
//   return (
//     <button
//       className={classes}
//       disabled={disabled || loading}
//       {...props}
//     >
//       {loading && (
//         <span className="mr-2">
//           <LoadingSpinner size="small" color="white" />
//         </span>
//       )}
//       {children}
//     </button>
//   );
// };
// export default Button;
