import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import assessmentResultsService from "../../services/assessmentResultsService";
import apiClient from "../../services/api";

interface MBTIResult {
  result_id: number;
  assessment_type: string;
  type: string;
  confidence: number;
  description: string;
  dimensions: Record<string, number>;
  preferences?: string[];
  strengths?: string[];
  blindSpots?: string[];
  completed_at: string;
}

const AssessmentResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<MBTIResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ✅ FIXED: Function moved inside useEffect to avoid dependency issues
  useEffect(() => {
    const loadAssessmentResults = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get the most recent result for this assessment type
        if (id === 'mbti') {
          // Try the test endpoint first (no authentication required)
          try {
            const testResponse = await apiClient.get('/assessment-results-test?assessment_type=mbti&limit=1');
            if (testResponse.data && (testResponse.data as any).success && (testResponse.data as any).count > 0) {
              const latestResult = (testResponse.data as any).results[0];
              setResults(latestResult as MBTIResult);
              return;
            }
          } catch (testError) {
            console.log('Test endpoint failed, trying authenticated endpoint...');
          }

          // Fallback to authenticated endpoint
          const response = await assessmentResultsService.getAssessmentResults('mbti', 1);
          if (response.success && response.results.length > 0) {
            const latestResult = response.results[0];
            setResults(latestResult as MBTIResult);
          } else {
            setError("No MBTI assessment results found. Please complete an assessment first.");
          }
        } else {
          setError(`Results for ${id} assessments are not yet implemented.`);
        }
      } catch (err) {
        console.error('Failed to load assessment results:', err);
        setError("Failed to load assessment results. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    loadAssessmentResults();
  }, [id]); // ✅ Only depends on id

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4">
            {error}
          </div>
          <Button variant="outline" onClick={() => navigate("/assessments")}>
            Back to Assessments
          </Button>
        </div>
      </div>
    );
  }

  if (!results || id !== 'mbti') {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-4 capitalize">{id} Results</h1>
        <p className="text-gray-600 mb-6">
          Results for <strong>{id}</strong> assessments are coming soon.
        </p>
        <Button variant="outline" onClick={() => navigate("/assessments")}>
          Back to Assessments
        </Button>
      </div>
    );
  }

  // Display MBTI Results
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Your MBTI Type: {results.type}
            </h1>
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-white text-2xl font-bold">{results.type}</span>
            </div>
            <p className="text-gray-600 mb-4">{results.description}</p>
            <p className="text-sm text-gray-500 mb-2">
              Confidence: {Math.round((results.confidence || 0) * 100)}%
            </p>
            <p className="text-xs text-gray-400">
              Completed on: {new Date(results.completed_at).toLocaleDateString()}
            </p>
          </div>

          {/* Personality Dimensions */}
          <div className="border-t pt-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Personality Dimensions</h3>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(results.dimensions || {}).map(([dimension, score]) => {
                const numScore = score as number;
                return (
                  <div key={dimension} className="text-center">
                    <div className="mb-2">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {dimension.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(numScore || 0) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">{Math.round((numScore || 0) * 100)}%</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths */}
          {results.strengths && results.strengths.length > 0 && (
            <div className="border-t pt-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Key Strengths</h3>
              <ul className="list-disc list-inside space-y-2">
                {results.strengths.slice(0, 4).map((strength, index) => (
                  <li key={index} className="text-gray-700">{strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Blind Spots */}
          {results.blindSpots && results.blindSpots.length > 0 && (
            <div className="border-t pt-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Growth Areas</h3>
              <ul className="list-disc list-inside space-y-2">
                {results.blindSpots.slice(0, 3).map((blindSpot, index) => (
                  <li key={index} className="text-gray-700">{blindSpot}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold mb-4">Next Steps</h3>
            <div className="space-y-3">
              <Button
                onClick={() => navigate("/assessments")}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Back to Assessments
              </Button>
              <Button
                onClick={() => navigate(`/assessments/${id}/start`)}
                variant="outline"
                className="w-full border border-gray-300 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Retake Assessment
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentResultsPage;
