# Complete PsychSync Refactoring Implementation Guide

## Backend Refactoring Steps

### Step 1: Create Core Configuration Files

Create the following files in your `app/core/` directory:

1. **`app/core/__init__.py`** (empty file)
2. **`app/core/config.py`** - Configuration management
3. **`app/core/database.py`** - Database setup
4. **`app/core/cache.py`** - Redis cache management  
5. **`app/core/middleware.py`** - Middleware configuration

### Step 2: Refactor AI Engine

Create AI engine directory structure:

```
app/ai/
├── __init__.py
├── engine/
│   ├── __init__.py
│   ├── behavioral_ai.py      # Main AI engine
│   ├── team_optimizer.py     # Team optimization logic
│   ├── compatibility.py      # Compatibility calculations
│   └── predictive_analytics.py # Predictive models
└── processors/
    ├── __init__.py
    ├── base.py               # Base processor class
    ├── enneagram.py          # Enneagram processor
    ├── mbti.py               # MBTI processor
    ├── big_five.py           # Big Five processor
    ├── predictive_index.py   # PI processor
    ├── strengths.py          # StrengthsFinder processor
    └── social_styles.py      # Social Styles processor
```

### Step 3: Update Database Setup

**`app/core/database.py`**:
```python
# app/core/database.py - Database Configuration

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 4: Create Remaining AI Processors

**`app/ai/processors/big_five.py`**:
```python
# app/ai/processors/big_five.py - Big Five Processor

from typing import Dict, Any, List
from app.ai.processors.base import PersonalityFrameworkProcessor

class BigFiveProcessor(PersonalityFrameworkProcessor):
    """Process Big Five assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Big Five data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('big_five', 'Invalid input data')
        
        try:
            dimensions = {}
            dimension_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            for dim in dimension_names:
                value = self._safe_get(raw_data, dim, 0.5)
                dimensions[dim] = self._clamp_value(float(value))
            
            return {
                'dimensions': dimensions,
                'confidence': self._safe_get(raw_data, 'confidence', 0.9),
                'interpretations': self._get_interpretations(dimensions),
                'percentiles': self._convert_to_percentiles(dimensions),
                'strengths': self._identify_strengths(dimensions),
                'development_areas': self._identify_development_areas(dimensions)
            }
            
        except Exception as e:
            return self._fallback_result('big_five', str(e))
    
    def _get_interpretations(self, dimensions: Dict[str, float]) -> Dict[str, str]:
        """Get interpretations for each dimension"""
        interpretations = {}
        
        for dim, value in dimensions.items():
            if value > 0.7:
                level = "High"
            elif value > 0.3:
                level = "Moderate"
            else:
                level = "Low"
            
            interpretations[dim] = f"{level} {dim.title()}"
        
        return interpretations
    
    def _convert_to_percentiles(self, dimensions: Dict[str, float]) -> Dict[str, int]:
        """Convert raw scores to percentiles"""
        return {dim: int(value * 100) for dim, value in dimensions.items()}
```

## Frontend Refactoring Steps

### Step 1: Create Context Files

Create these files in `src/contexts/`:

1. **`src/contexts/AuthContext.tsx`** - Authentication management
2. **`src/contexts/NotificationContext.tsx`** - Notification system
3. **`src/contexts/TeamContext.tsx`** - Team management

**`src/contexts/TeamContext.tsx`**:
```typescript
// src/contexts/TeamContext.tsx - Team Management Context

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Team, ApiResponse } from '../types';
import { useNotification } from './NotificationContext';

interface TeamContextType {
  teams: Team[];
  currentTeam: Team | null;
  loading: boolean;
  fetchTeams: () => Promise<void>;
  createTeam: (teamData: Omit<Team, 'id'>) => Promise<ApiResponse<Team>>;
  updateTeam: (teamId: number, updateData: Partial<Team>) => Promise<ApiResponse<Team>>;
  deleteTeam: (teamId: number) => Promise<ApiResponse>;
  selectTeam: (team: Team) => void;
}

const TeamContext = createContext<TeamContextType | undefined>(undefined);

export const useTeam = (): TeamContextType => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};

interface TeamProviderProps {
  children: ReactNode;
}

export const TeamProvider: React.FC<TeamProviderProps> = ({ children }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { showNotification } = useNotification();

  const fetchTeams = async (): Promise<void> => {
    setLoading(true);
    try {
      // Mock data - replace with actual API call
      const mockTeams: Team[] = [
        { id: 1, name: 'Frontend Team', status: 'active', description: 'Web development team' },
        { id: 2, name: 'Backend Team', status: 'active', description: 'API development team' },
        { id: 3, name: 'QA Team', status: 'inactive', description: 'Quality assurance team' },
      ];
      setTeams(mockTeams);
    } catch (error) {
      showNotification('Failed to fetch teams', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createTeam = async (teamData: Omit<Team, 'id'>): Promise<ApiResponse<Team>> => {
    try {
      const newTeam: Team = { id: Date.now(), ...teamData, status: 'active' };
      setTeams((prev) => [...prev, newTeam]);
      showNotification('Team created successfully', 'success');
      return { success: true, data: newTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const updateTeam = async (teamId: number, updateData: Partial<Team>): Promise<ApiResponse<Team>> => {
    try {
      const updatedTeam: Team = { ...updateData, id: teamId } as Team;
      setTeams((prev) => prev.map((team) => team.id === teamId ? { ...team, ...updatedTeam } : team));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam({ ...currentTeam, ...updatedTeam });
      }
      showNotification('Team updated successfully', 'success');
      return { success: true, data: updatedTeam };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const deleteTeam = async (teamId: number): Promise<ApiResponse> => {
    try {
      setTeams((prev) => prev.filter((team) => team.id !== teamId));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam(null);
      }
      showNotification('Team deleted successfully', 'success');
      return { success: true };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete team';
      showNotification(errorMessage, 'error');
      return { success: false, error: errorMessage };
    }
  };

  const selectTeam = (team: Team): void => {
    setCurrentTeam(team);
  };

  const value: TeamContextType = {
    teams, currentTeam, loading, fetchTeams, createTeam, updateTeam, deleteTeam, selectTeam,
  };

  return <TeamContext.Provider value={value}>{children}</TeamContext.Provider>;
};
```

### Step 2: Create Component Files

Create component directory structure:

```
src/components/
├── common/
│   ├── Button.tsx
│   ├── LoadingSpinner.tsx
│   └── NotificationContainer.tsx
├── layout/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── Layout.tsx
└── ui/
    └── (additional UI components)
```

**`src/components/common/Button.tsx`**:
```typescript
// src/components/common/Button.tsx - Reusable Button Component

import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled,
  className = '',
  children,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };
  
  const sizeClasses = {
    small: 'px-3 py-2 text-sm',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base',
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  
  return (
    <button
      className={classes}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
};

export default Button;
```

### Step 3: Create Type Definitions

**`src/types/index.ts`**:
```typescript
// src/types/index.ts - Main Type Definitions

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Team {
  id: number;
  name: string;
  status: 'active' | 'inactive';
  description: string;
}

export interface Notification {
  id: number;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface DashboardData {
  totalTeams: number;
  totalAssessments: number;
  avgCompatibility: number;
  predictedVelocity: number;
}
```

### Step 4: Update Main App Component

**`src/App.tsx`**:
```typescript
// src/App.tsx - Clean Main Application Component

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { TeamProvider } from './contexts/TeamContext';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import LoadingSpinner from './components/common/LoadingSpinner';

const AppRoutes: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">Loading PsychSync...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        {/* Add other routes here */}
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <NotificationProvider>
        <TeamProvider>
          <Router>
            <AppRoutes />
          </Router>
        </TeamProvider>
      </NotificationProvider>
    </AuthProvider>
  );
};

export default App;
```

## Migration Steps

### Backend Migration:
1. Create new directory structure
2. Move existing code to new files
3. Update imports throughout the codebase
4. Test each module independently
5. Update main.py to use new structure

### Frontend Migration:
1. Create contexts directory and move context code
2. Create components directory structure  
3. Extract components from App.tsx
4. Update imports and routes
5. Test each component independently

## Benefits Achieved:
- **Separation of Concerns**: Each file has a single responsibility
- **Reusability**: Components and utilities can be reused
- **Maintainability**: Easier to find and modify specific functionality
- **Testing**: Each module can be tested in isolation
- **Scalability**: Easy to add new features without affecting existing code
- **Team Collaboration**: Multiple developers can work on different modules

This refactoring transforms the monolithic codebase into a clean, modular architecture that follows industry best practices.