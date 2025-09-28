// // // // // src/components/LoadingSpinner.tsx

// src/components/LoadingSpinner.tsx
import React from 'react';
import { LoadingSpinnerProps } from '../types/components';

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium',
  color = 'blue-600' 
}) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };

  return (
    <div className={`animate-spin rounded-full border-b-2 border-${color} ${sizeClasses[size]}`} />
  );
};

export default LoadingSpinner;

// // src/components/LoadingSpinner.tsx
// import React from "react";

// interface LoadingSpinnerProps {
//   size?: number;
// }

// const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 40 }) => {
//   return (
//     <div
//       style={{
//         width: size,
//         height: size,
//         border: "4px solid #ccc",
//         borderTop: "4px solid #333",
//         borderRadius: "50%",
//         animation: "spin 1s linear infinite",
//       }}
//     />
//   );
// };

// export default LoadingSpinner;



// // import React from "react";

// // export interface LoadingSpinnerProps {
// //   size?: number;
// //   color?: string;
// // }

// // const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
// //   size = 24,
// //   color = "black",
// // }) => (
// //   <div
// //     style={{
// //       width: size,
// //       height: size,
// //       border: `2px solid ${color}`,
// //       borderTop: "2px solid transparent",
// //       borderRadius: "50%",
// //       animation: "spin 1s linear infinite",
// //     }}
// //   />
// // );

// // export default LoadingSpinner;

// // // // src/components/LoadingSpinner.tsx
// // // import React from "react";

// // // export interface LoadingSpinnerProps {
// // //   size?: number;
// // //   color?: string;
// // // }

// // // const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
// // //   size = 24,
// // //   color = "black",
// // // }) => (
// // //   <div
// // //     style={{
// // //       width: size,
// // //       height: size,
// // //       border: `2px solid ${color}`,
// // //       borderTop: "2px solid transparent",
// // //       borderRadius: "50%",
// // //       animation: "spin 1s linear infinite",
// // //     }}
// // //   />
// // // );

// // // export default LoadingSpinner; // ✅ now App.tsx can use `import LoadingSpinner`

// // // // import React from "react";
// // // // import { LoadingSpinnerProps } from "../types/components";

// // // // export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 24, color = "blue" }) => {
// // // //   return (
// // // //     <div
// // // //       style={{
// // // //         width: size,
// // // //         height: size,
// // // //         border: `2px solid ${color}`,
// // // //         borderTop: "2px solid transparent",
// // // //         borderRadius: "50%",
// // // //         animation: "spin 1s linear infinite"
// // // //       }}
// // // //     />
// // // //   );
// // // // };

// // // // // import React from 'react';
// // // // // import { LoadingSpinnerProps } from '../types/components';

// // // // // export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
// // // // //   size = 'medium',
// // // // //   color = 'blue-600'
// // // // // }) => {
// // // // //   // Component implementation
// // // // // };
