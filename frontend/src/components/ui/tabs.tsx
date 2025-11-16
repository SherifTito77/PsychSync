import React from 'react';
interface TabsProps {
  children: React.ReactNode;
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
}
export const Tabs: React.FC<TabsProps> = ({
  children,
  defaultValue,
  value,
  onValueChange,
  className = ''
}) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue || '');
  const handleTabChange = (tabValue: string) => {
    setActiveTab(tabValue);
    onValueChange?.(tabValue);
  };
  const currentTab = value !== undefined ? value : activeTab;
  return (
    <div className={className}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            activeTab: currentTab,
            onTabChange: handleTabChange
          });
        }
        return child;
      })}
    </div>
  );
};
interface TabsListProps {
  children: React.ReactNode;
  className?: string;
  activeTab?: string;
  onTabChange?: (value: string) => void;
}
export const TabsList: React.FC<TabsListProps> = ({
  children,
  className = 'border-b border-gray-200',
  activeTab,
  onTabChange
}) => {
  return (
    <div className={`flex space-x-8 ${className}`}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            activeTab,
            onTabChange
          });
        }
        return child;
      })}
    </div>
  );
};
interface TabsTriggerProps {
  children: React.ReactNode;
  value: string;
  className?: string;
  activeTab?: string;
  onTabChange?: (value: string) => void;
}
export const TabsTrigger: React.FC<TabsTriggerProps> = ({
  children,
  value,
  className = '',
  activeTab,
  onTabChange
}) => {
  const isActive = activeTab === value;
  const baseClasses = 'py-2 px-1 border-b-2 font-medium text-sm transition-colors';
  const activeClasses = isActive
    ? 'border-blue-500 text-blue-600'
    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300';
  return (
    <button
      className={`${baseClasses} ${activeClasses} ${className}`}
      onClick={() => onTabChange?.(value)}
    >
      {children}
    </button>
  );
};
interface TabsContentProps {
  children: React.ReactNode;
  value: string;
  className?: string;
  activeTab?: string;
}
export const TabsContent: React.FC<TabsContentProps> = ({
  children,
  value,
  className = 'mt-4',
  activeTab
}) => {
  if (activeTab !== value) {
    return null;
  }
  return <div className={className}>{children}</div>;
};