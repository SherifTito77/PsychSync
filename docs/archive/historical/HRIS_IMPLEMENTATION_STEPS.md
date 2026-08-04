# 🚀 Next Steps: Use HRIS Data in Your Features

## ✅ Quick Start (5 Minutes)

### Step 1: Use the Custom Hook
Copy this hook to your project:
```bash
✅ Already created: frontend/src/hooks/useHRISData.ts
```

### Step 2: Import & Use in Any Component
```typescript
import { useHRISData } from '@/hooks/useHRISData';

const MyComponent = () => {
  const { employees, getEmployeeById, getEmployeesByDepartment } = useHRISData();

  return (
    <div>
      <h1>Total Employees: {employees.length}</h1>
      {employees.map(emp => (
        <div key={emp.id}>{emp.name} - {emp.department}</div>
      ))}
    </div>
  );
};
```

---

## 🎯 3 Practical Implementations

### Option 1: Quick Win - Add HRIS Data to Dashboard ⭐ (START HERE)

**File to modify**: `frontend/src/pages/Dashboard.tsx`

**Add this code**:
```typescript
import { useHRISData } from '@/hooks/useHRISData';

const Dashboard = () => {
  const { employees, departments } = useHRISData();

  // Add HRIS metrics section
  return (
    <div>
      {/* Your existing dashboard content */}

      {/* NEW: HRIS Quick Stats */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>👥 HRIS Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{employees.length}</div>
              <div className="text-sm text-gray-600">Total Employees</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{departments.length}</div>
              <div className="text-sm text-gray-600">Departments</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">100%</div>
              <div className="text-sm text-gray-600">Active Status</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

**Result**: Dashboard now shows employee count from HRIS!

---

### Option 2: Add HRIS Filter to Team Optimizer

**File to modify**: `frontend/src/pages/TeamOptimizer.tsx`

**Add department filter**:
```typescript
import { useHRISData } from '@/hooks/useHRISData';

const TeamOptimizer = () => {
  const { employees, departments, getEmployeesByDepartment } = useHRISData();
  const [selectedDept, setSelectedDept] = useState<string>('All');

  const filteredEmployees = selectedDept === 'All'
    ? employees
    : getEmployeesByDepartment(selectedDept);

  return (
    <div>
      {/* NEW: Department Filter */}
      <div className="mb-4">
        <label>Filter by Department: </label>
        <select onChange={(e) => setSelectedDept(e.target.value)}>
          <option value="All">All Departments</option>
          {departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>
      </div>

      {/* Your existing team optimizer shows filtered employees */}
      <div>Showing {filteredEmployees.length} employees</div>
    </div>
  );
};
```

**Result**: Team optimizer now filters by HRIS departments!

---

### Option 3: Create HRIS-Powered Analytics Page

**Create new file**: `frontend/src/pages/HRISAnalytics.tsx`

```typescript
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHRISData } from '@/hooks/useHRISData';

export const HRISAnalytics: React.FC = () => {
  const { employees, departments, getEmployeesByDepartment } = useHRISData();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">📊 HRIS-Powered Analytics</h1>

      {/* Department Distribution */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>🏢 Department Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {departments.map(dept => {
              const deptEmployees = getEmployeesByDepartment(dept);
              const percentage = (deptEmployees.length / employees.length) * 100;
              return (
                <div key={dept} className="bg-blue-50 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {deptEmployees.length}
                  </div>
                  <div className="text-sm text-gray-600">{dept}</div>
                  <div className="text-xs text-gray-500">{percentage.toFixed(0)}%</div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Position Breakdown */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>💼 Position Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from(new Set(employees.map(e => e.position))).map(position => {
              const positionCount = employees.filter(e => e.position === position).length;
              return (
                <div key={position} className="flex justify-between items-center border-b pb-2">
                  <span>{position}</span>
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                    {positionCount} employees
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Employee Directory */}
      <Card>
        <CardHeader>
          <CardTitle>👥 Employee Directory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {employees.map(emp => (
              <div key={emp.id} className="border rounded-lg p-4">
                <div className="font-semibold text-lg">{emp.name}</div>
                <div className="text-sm text-gray-600">{emp.position}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {emp.department} • {emp.location}
                </div>
                <div className="mt-2">
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                    {emp.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

**Add to router**: In `App.tsx`, add:
```typescript
import { HRISAnalytics } from './pages/HRISAnalytics';

// In your routes:
<Route path="/hris-analytics" element={<HRISAnalytics />} />
```

**Result**: New analytics page powered by HRIS data!

---

## 🔗 Connect HRIS to Assessment Data

### Example: Link Employees to Their Assessments

```typescript
import { useHRISData } from '@/hooks/useHRISData';
import { useAssessments } from '@/hooks/useAssessments'; // Your existing hook

const EmployeeAssessments = () => {
  const { employees } = useHRISData();
  const { assessments } = useAssessments();

  // Combine HRIS data with assessment results
  const employeeData = employees.map(emp => {
    const empAssessments = assessments.filter(a => a.employee_id === emp.id);
    return {
      ...emp,
      assessments: empAssessments,
      lastAssessment: empAssessments[0]?.date || null
    };
  });

  return (
    <table>
      <thead>
        <tr>
          <th>Employee</th>
          <th>Department</th>
          <th>Assessments Completed</th>
          <th>Last Assessment</th>
        </tr>
      </thead>
      <tbody>
        {employeeData.map(emp => (
          <tr key={emp.id}>
            <td>{emp.name}</td>
            <td>{emp.department}</td>
            <td>{emp.assessments.length}</td>
            <td>{emp.lastAssessment || 'Not completed'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

---

## 📋 Implementation Checklist

Choose your path:

### ⭐ Path A: Quick & Easy (Recommended for starting)
- [ ] Import `useHRISData` hook into Dashboard
- [ ] Add employee count display
- [ ] Test with demo data
- [ ] Commit changes

### 🚀 Path B: Moderate Effort
- [ ] Create HRISAnalytics page
- [ ] Add to router
- [ ] Test all views
- [ ] Add link in navigation

### 💪 Path C: Full Integration
- [ ] Add HRIS data to TeamOptimizer
- [ ] Link employees to assessments
- [ ] Create combined analytics
- [ ] Add department filtering everywhere

---

## 🧪 Test Your Integration

### 1. Test the Hook
```typescript
// In any component
const { employees, departments } = useHRISData();
console.log('Employees:', employees);
console.log('Departments:', departments);
```

### 2. Verify Demo Data
You should see:
- 5 employees
- 5 departments (Administration, IT, Sales, HR, Finance)
- All employees marked as "Active"

### 3. Test Filter
```typescript
const itEmployees = getEmployeesByDepartment('IT');
console.log('IT Employees:', itEmployees);
// Should show: John Dickens
```

---

## 🎯 What This Enables

Once HRIS data is flowing:

1. **Team Optimization** by department
2. **Assessment completion tracking** per employee
3. **Department-level analytics**
4. **Employee-specific insights**
5. **Org-aware team composition**
6. **Targeted training programs**
7. **Succession planning**

---

## 💡 Pro Tips

1. **Start Simple**: Add employee count to dashboard first
2. **Test Thoroughly**: Verify demo data displays correctly
3. **Expand Gradually**: Add more features as you get comfortable
4. **Keep Privacy**: Don't display sensitive HRIS data publicly
5. **Validate Data**: Always check if data exists before rendering

---

`★ Insight ─────────────────────────────────────`
**Custom Hook Pattern**: The `useHRISData` hook encapsulates all HRIS data fetching logic. This keeps your components clean and makes it easy to swap data sources later (from demo to real HRIS).

**Progressive Enhancement**: Start with basic employee listing, then add filtering, then add assessment linking. Each step builds on the previous one and provides immediate value.

**Separation of Concerns**: Notice how HRIS data fetching is separate from assessment data. This makes your code more maintainable and easier to test.
`─────────────────────────────────────────────────`

---

## 🚀 Ready to Start?

**Pick ONE option and implement it now:**

1. ⭐ **Quick Win** (5 min): Add employee count to Dashboard
2. 🚀 **Moderate** (15 min): Create HRISAnalytics page
3. 💪 **Full** (30 min): Add HRIS to TeamOptimizer

**Which one would you like to implement first?**
