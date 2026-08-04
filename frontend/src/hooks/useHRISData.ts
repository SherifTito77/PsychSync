// useHRISData.ts - Enhanced Custom Hook with Assessment Integration
import { useState, useEffect, useMemo } from 'react';
import { Employee, EmployeeAssessmentData, DepartmentAnalytics, HRISStatistics } from '@/types/hris';
import api from '@/services/api';

// Demo data with assessments
const demoEmployeesWithAssessments: Employee[] = [
  {
    id: 'EMP001',
    name: 'Admin User',
    email: 'admin@psychsync.com',
    position: 'Administrator',
    department: 'Administration',
    location: 'Headquarters',
    status: 'Active',
    hire_date: '2020-01-15',
    assessment_data: {
      last_assessment_date: '2024-01-10',
      assessments_completed: 5,
      personality_profile: {
        openness: 75,
        conscientiousness: 85,
        extraversion: 70,
        agreeableness: 80,
        neuroticism: 35,
        dominant_traits: ['Conscientious', 'Agreeable'],
        communication_style: 'Collaborative',
        work_style: 'Structured'
      },
      big_five_scores: {
        openness: 75,
        conscientiousness: 85,
        extraversion: 70,
        agreeableness: 80,
        neuroticism: 35
      },
      mbti_type: 'ESTJ-A',
      emotional_intelligence: 82,
      leadership_potential: 88,
      team_fit_score: 85,
      strengths: ['Leadership', 'Organization', 'Communication'],
      development_areas: ['Delegation', 'Work-Life Balance']
    }
  },
  {
    id: 'EMP002',
    name: 'John Dickens',
    email: 'john.d@psychsync.com',
    position: 'Software Engineer',
    department: 'IT',
    location: 'Headquarters',
    status: 'Active',
    hire_date: '2021-03-20',
    assessment_data: {
      last_assessment_date: '2024-01-08',
      assessments_completed: 4,
      personality_profile: {
        openness: 90,
        conscientiousness: 75,
        extraversion: 55,
        agreeableness: 65,
        neuroticism: 45,
        dominant_traits: ['Open', 'Analytical'],
        communication_style: 'Direct',
        work_style: 'Autonomous'
      },
      big_five_scores: {
        openness: 90,
        conscientiousness: 75,
        extraversion: 55,
        agreeableness: 65,
        neuroticism: 45
      },
      mbti_type: 'INTJ-A',
      emotional_intelligence: 70,
      leadership_potential: 72,
      team_fit_score: 78,
      strengths: ['Problem Solving', 'Innovation', 'Technical Skills'],
      development_areas: ['Team Collaboration', 'Communication']
    }
  },
  {
    id: 'EMP003',
    name: 'Jane Doe',
    email: 'jane.d@psychsync.com',
    position: 'Sales Manager',
    department: 'Sales',
    location: 'Branch Office',
    status: 'Active',
    hire_date: '2020-07-12',
    assessment_data: {
      last_assessment_date: '2024-01-12',
      assessments_completed: 6,
      personality_profile: {
        openness: 80,
        conscientiousness: 70,
        extraversion: 95,
        agreeableness: 85,
        neuroticism: 40,
        dominant_traits: ['Extraverted', 'Agreeable'],
        communication_style: 'Persuasive',
        work_style: 'Collaborative'
      },
      big_five_scores: {
        openness: 80,
        conscientiousness: 70,
        extraversion: 95,
        agreeableness: 85,
        neuroticism: 40
      },
      mbti_type: 'ENFJ-A',
      emotional_intelligence: 91,
      leadership_potential: 85,
      team_fit_score: 90,
      strengths: ['Communication', 'Relationship Building', 'Motivation'],
      development_areas: ['Patience', 'Detail Orientation']
    }
  },
  {
    id: 'EMP004',
    name: 'Bob Smith',
    email: 'bob.s@psychsync.com',
    position: 'HR Manager',
    department: 'HR',
    location: 'Headquarters',
    status: 'Active',
    hire_date: '2019-11-05',
    assessment_data: {
      last_assessment_date: '2024-01-05',
      assessments_completed: 7,
      personality_profile: {
        openness: 75,
        conscientiousness: 80,
        extraversion: 78,
        agreeableness: 92,
        neuroticism: 30,
        dominant_traits: ['Agreeable', 'Empathetic'],
        communication_style: 'Supportive',
        work_style: 'People-Oriented'
      },
      big_five_scores: {
        openness: 75,
        conscientiousness: 80,
        extraversion: 78,
        agreeableness: 92,
        neuroticism: 30
      },
      mbti_type: 'ESFJ-A',
      emotional_intelligence: 95,
      leadership_potential: 80,
      team_fit_score: 92,
      strengths: ['Empathy', 'Conflict Resolution', 'Team Building'],
      development_areas: ['Strategic Thinking', 'Data Analysis']
    }
  },
  {
    id: 'EMP005',
    name: 'Alice Williams',
    email: 'alice.w@psychsync.com',
    position: 'Accountant',
    department: 'Finance',
    location: 'Headquarters',
    status: 'Active',
    hire_date: '2021-09-18',
    assessment_data: {
      last_assessment_date: '2024-01-14',
      assessments_completed: 3,
      personality_profile: {
        openness: 60,
        conscientiousness: 95,
        extraversion: 45,
        agreeableness: 75,
        neuroticism: 50,
        dominant_traits: ['Conscientious', 'Detail-Oriented'],
        communication_style: 'Precise',
        work_style: 'Structured'
      },
      big_five_scores: {
        openness: 60,
        conscientiousness: 95,
        extraversion: 45,
        agreeableness: 75,
        neuroticism: 50
      },
      mbti_type: 'ISTJ-A',
      emotional_intelligence: 75,
      leadership_potential: 68,
      team_fit_score: 82,
      strengths: ['Accuracy', 'Organization', 'Compliance'],
      development_areas: ['Adaptability', 'Risk Taking']
    }
  }
];

export const useHRISData = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useRealAPI, setUseRealAPI] = useState(false);

  useEffect(() => {
    fetchHRISData();
  }, [useRealAPI]);

  const fetchHRISData = async () => {
    setLoading(true);
    setError(null);

    try {
      if (useRealAPI) {
        // Call real HRIS API
        const response = await api.get('/hris/employees');
        setEmployees(response.data.employees);
      } else {
        // Use demo data
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 800));
        setEmployees(demoEmployeesWithAssessments);
      }
    } catch (err: any) {
      console.error('HRIS API Error:', err);
      setError(err.message || 'Failed to fetch HRIS data');
      // Fallback to demo data on error
      setEmployees(demoEmployeesWithAssessments);
    } finally {
      setLoading(false);
    }
  };

  const getEmployeeById = (id: string): Employee | undefined => {
    return employees.find(emp => emp.id === id);
  };

  const getEmployeesByDepartment = (department: string): Employee[] => {
    return employees.filter(emp => emp.department === department);
  };

  const getEmployeesByLocation = (location: string): Employee[] => {
    return employees.filter(emp => emp.location === location);
  };

  // Calculate enhanced statistics with assessment data
  const calculateStatistics = (): HRISStatistics => {
    if (employees.length === 0) {
      return {
        totalEmployees: 0,
        totalDepartments: 0,
        totalPositions: 0,
        totalLocations: 0,
        activePercentage: 0,
        departmentCounts: [],
        positionCounts: {},
        locationCounts: {}
      };
    }

    const departments = [...new Set(employees.map(e => e.department))];
    const positions = [...new Set(employees.map(e => e.position))];
    const locations = [...new Set(employees.map(e => e.location))];

    const departmentCounts = departments.map(dept => ({
      name: dept,
      count: getEmployeesByDepartment(dept).length,
      percentage: (getEmployeesByDepartment(dept).length / employees.length) * 100
    }));

    const positionCounts = employees.reduce((acc, emp) => {
      acc[emp.position] = (acc[emp.position] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const locationCounts = employees.reduce((acc, emp) => {
      acc[emp.location] = (acc[emp.location] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const activeCount = employees.filter(e => e.status === 'Active').length;

    // Assessment-specific statistics
    const employeesWithAssessments = employees.filter(e => e.assessment_data);
    const assessmentCompletionRate = (employeesWithAssessments.length / employees.length) * 100;

    const avgLeadershipPotential = employeesWithAssessments.length > 0
      ? employeesWithAssessments.reduce((sum, e) => sum + (e.assessment_data?.leadership_potential || 0), 0) / employeesWithAssessments.length
      : 0;

    // Trait distribution
    const traitDistribution = employeesWithAssessments.reduce((acc, emp) => {
      const traits = emp.assessment_data?.personality_profile?.dominant_traits || [];
      traits.forEach(trait => {
        acc[trait] = (acc[trait] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    return {
      totalEmployees: employees.length,
      totalDepartments: departments.length,
      totalPositions: positions.length,
      totalLocations: locations.length,
      activePercentage: (activeCount / employees.length) * 100,
      assessmentCompletionRate,
      avgLeadershipPotential,
      departmentCounts,
      positionCounts,
      locationCounts,
      traitDistribution
    };
  };

  // Enhanced department analytics
  const getDepartmentAnalytics = (): DepartmentAnalytics[] => {
    const departments = [...new Set(employees.map(e => e.department))];

    return departments.map(dept => {
      const deptEmployees = getEmployeesByDepartment(dept);
      const employeesWithAssessments = deptEmployees.filter(e => e.assessment_data);

      const avgLeadership = employeesWithAssessments.length > 0
        ? employeesWithAssessments.reduce((sum, e) => sum + (e.assessment_data?.leadership_potential || 0), 0) / employeesWithAssessments.length
        : 0;

      const avgTeamFit = employeesWithAssessments.length > 0
        ? employeesWithAssessments.reduce((sum, e) => sum + (e.assessment_data?.team_fit_score || 0), 0) / employeesWithAssessments.length
        : 0;

      // Get top traits for this department
      const traitCounts: Record<string, number> = {};
      employeesWithAssessments.forEach(emp => {
        const traits = emp.assessment_data?.personality_profile?.dominant_traits || [];
        traits.forEach(trait => {
          traitCounts[trait] = (traitCounts[trait] || 0) + 1;
        });
      });

      const topTraits = Object.entries(traitCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 3)
        .map(([trait]) => trait);

      return {
        name: dept,
        employee_count: deptEmployees.length,
        percentage: (deptEmployees.length / employees.length) * 100,
        avg_leadership_potential: avgLeadership,
        avg_team_fit: avgTeamFit,
        top_traits: topTraits,
        assessment_completion_rate: (employeesWithAssessments.length / deptEmployees.length) * 100
      };
    });
  };

  const stats = useMemo(calculateStatistics, [employees]);
  const departmentAnalytics = useMemo(getDepartmentAnalytics, [employees]);

  const toggleAPISource = () => {
    setUseRealAPI(prev => !prev);
  };

  return {
    employees,
    loading,
    error,
    useRealAPI,
    stats,
    departmentAnalytics,
    getEmployeeById,
    getEmployeesByDepartment,
    getEmployeesByLocation,
    toggleAPISource,
    totalEmployees: employees.length,
    departments: [...new Set(employees.map(e => e.department))]
  };
};
