import React from 'react';
interface TableProps {
  children: React.ReactNode;
  className?: string;
}
export const Table: React.FC<TableProps> = ({ children, className = '' }) => {
  return <table className={`w-full border-collapse ${className}`}>{children}</table>;
};
interface TableHeaderProps {
  children: React.ReactNode;
  className?: string;
}
export const TableHeader: React.FC<TableHeaderProps> = ({ children, className = '' }) => {
  return <thead className={`bg-gray-50 ${className}`}>{children}</thead>;
};
interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}
export const TableBody: React.FC<TableBodyProps> = ({ children, className = '' }) => {
  return <tbody className={className}>{children}</tbody>;
};
interface TableRowProps {
  children: React.ReactNode;
  className?: string;
}
export const TableRow: React.FC<TableRowProps> = ({ children, className = '' }) => {
  return <tr className={`border-b ${className}`}>{children}</tr>;
};
interface TableCellProps {
  children: React.ReactNode;
  className?: string;
}
export const TableCell: React.FC<TableCellProps> = ({ children, className = 'px-4 py-2 text-left' }) => {
  return <td className={className}>{children}</td>;
};
interface TableHeadProps {
  children: React.ReactNode;
  className?: string;
}
export const TableHead: React.FC<TableHeadProps> = ({ children, className = 'px-4 py-2 text-left font-medium text-gray-900' }) => {
  return <th className={className}>{children}</th>;
};