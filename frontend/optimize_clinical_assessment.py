#!/usr/bin/env python3
"""
Script to optimize ClinicalAssessment.tsx for performance
- Extract question bank to separate file
- Add React.memo
- Add useMemo for expensive calculations
- Add useCallback for event handlers
- Move assessment configs to constants
"""

import re


def optimize_clinical_assessment():
    input_file = "frontend/src/pages/ClinicalAssessment.tsx"
    output_file = "frontend/src/pages/ClinicalAssessment.tsx"

    with open(input_file, "r") as f:
        content = f.read()

    # Step 1: Update imports to include useMemo and useCallback
    old_imports = "import React, { useState, useEffect } from 'react';"
    new_imports = (
        "import React, { useState, useEffect, useMemo, useCallback } from 'react';"
    )
    content = content.replace(old_imports, new_imports)

    # Step 2: Add imports from extracted files
    import_section = """import { Question, getRandomQuestions, getPreviousQuestionIds, saveQuestionIds } from './data/phq9-question-bank';
import { BASE_ASSESSMENTS, getAssessmentConfig, AssessmentData } from './config/assessment-configs';"""

    # Find where to insert the new imports (after Alert import)
    alert_import = "import { Alert } from '@/components/ui/alert';"
    if import_section.split("\n")[0] not in content:
        content = content.replace(alert_import, alert_import + "\n" + import_section)

    # Step 3: Remove the massive Question interface and PHQ9_QUESTION_BANK array (lines 68-688)
    # This is complex, so we'll use regex to remove it
    pattern = r"interface Question \{[^}]+\}.*?(?=\n// Function to generate random|const getRandomQuestions)"
    content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Also remove the old function definitions that are now imported
    # Remove the old getRandomQuestions, getPreviousQuestionIds, saveQuestionIds functions
    old_functions_pattern = (
        r"// Function to generate random.*?(?=\ninterface AssessmentData)"
    )
    content = re.sub(old_functions_pattern, "", content, flags=re.DOTALL)

    # Step 4: Remove the AssessmentData interface (it's now imported)
    # And remove the old assessments object
    assessments_pattern = (
        r"interface AssessmentData \{[^}]+\}\n\nconst ClinicalAssessment"
    )
    content = re.sub(assessments_pattern, "const ClinicalAssessment", content)

    # Step 5: Remove the inline assessments object (lines 774-831)
    old_assessments = r"  // Assessment configurations with dynamic question generation\n  const assessments: Record<string, AssessmentData> = \{[^}]+\{[^}]+\}[^}]+\};\n\n"
    content = re.sub(old_assessments, "", content, flags=re.DOTALL)

    # Step 6: Wrap component with React.memo
    old_export = "export default ClinicalAssessment;"
    new_export = """export default React.memo(ClinicalAssessment);"""
    content = content.replace(old_export, new_export)

    # Step 7: Add useMemo for calculateScore function
    # Find the calculateScore function and wrap it with useMemo
    old_calculate = """  const calculateScore = (): number => {
    if (!assessmentData) return 0;

    return assessmentData.questions.reduce((total, question) => {
      const response = responses[question.id];
      if (!response) return total;

      const optionValues = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'];
      const baseScore = optionValues.indexOf(response);
      const weightedScore = baseScore * question.severity_weight;
      return total + weightedScore;
    }, 0);
  };"""

    new_calculate = """  const calculateScore = useMemo((): number => {
    if (!assessmentData) return 0;

    return assessmentData.questions.reduce((total, question) => {
      const response = responses[question.id];
      if (!response) return total;

      const optionValues = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'];
      const baseScore = optionValues.indexOf(response);
      const weightedScore = baseScore * question.severity_weight;
      return total + weightedScore;
    }, 0);
  }, [assessmentData, responses]);"""

    content = content.replace(old_calculate, new_calculate)

    # Step 8: Add useCallback for event handlers
    old_handle_response = """  const handleResponseChange = (questionId: string, response: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: response,
    }));
  };"""

    new_handle_response = """  const handleResponseChange = useCallback((questionId: string, response: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: response,
    }));
  }, []);"""

    content = content.replace(old_handle_response, new_handle_response)

    old_handle_next = """  const handleNext = () => {
    if (!assessmentData) return;

    if (currentQuestion < assessmentData.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };"""

    new_handle_next = """  const handleNext = useCallback(() => {
    if (!assessmentData) return;

    if (currentQuestion < assessmentData.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      handleSubmit();
    }
  }, [assessmentData, currentQuestion, handleSubmit]);"""

    content = content.replace(old_handle_next, new_handle_next)

    old_handle_previous = """  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };"""

    new_handle_previous = """  const handlePrevious = useCallback(() => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  }, []);"""

    content = content.replace(old_handle_previous, new_handle_previous)

    # Step 9: Memoize getSeverityLevel
    old_get_severity = """  const getSeverityLevel = (score: number) => {
    if (!assessmentData) return null;

    return assessmentData.scoring.levels.find(level =>
      score >= level.range[0] && score <= level.range[1]
    );
  };"""

    new_get_severity = """  const getSeverityLevel = useCallback((score: number) => {
    if (!assessmentData) return null;

    return assessmentData.scoring.levels.find(level =>
      score >= level.range[0] && score <= level.range[1]
    );
  }, [assessmentData]);"""

    content = content.replace(old_get_severity, new_get_severity)

    # Step 10: Memoize handleSubmit
    old_handle_submit = """  const handleSubmit = async () => {"""

    # Find handleSubmit and wrap it
    # This is more complex because it's a large function, so we'll just find the start
    content = content.replace(
        "  const handleSubmit = async () => {",
        "  const handleSubmit = useCallback(async () => {",
    )

    # Add closing bracket and dependencies for handleSubmit
    # Find the end of handleSubmit function (look for the closing }; before the if (loading) check)
    content = re.sub(
        r"(    } finally \{\n      setSubmitting\(false\);\n    \}\n  \});",
        r"""    } finally {
        setSubmitting(false);
      }
    }, [assessmentData, tool, responses, showCrisisWarning, calculateScore, getSeverityLevel, navigate]);""",
        content,
    )

    # Write the optimized content
    with open(output_file, "w") as f:
        f.write(content)

    print("✅ ClinicalAssessment.tsx optimized successfully!")
    print("   - Added React.memo")
    print("   - Added useMemo for calculateScore")
    print("   - Added useCallback for event handlers")
    print("   - Question bank moved to separate file (needs to be created)")
    print("   - Assessment configs extracted (needs to be created)")


if __name__ == "__main__":
    optimize_clinical_assessment()
