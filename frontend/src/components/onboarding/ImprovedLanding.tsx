// src/components/onboarding/ImprovedLanding.tsx
// Value-first landing page that immediately shows product benefit
import React, { useState } from 'react';
import QuickValuePreview from './QuickValuePreview';
import StreamlinedRegister from './StreamlinedRegister';

interface ImprovedLandingProps {
  onGetStarted: (role: string, challenge: string) => void;
}

const ImprovedLanding: React.FC<ImprovedLandingProps> = ({ onGetStarted }) => {
  const [currentView, setCurrentView] = useState<'landing' | 'preview' | 'signup'>('landing');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedChallenge, setSelectedChallenge] = useState<string>('');

  const handlePreviewStart = (role: string, challenge: string) => {
    setSelectedRole(role);
    setSelectedChallenge(challenge);
    setCurrentView('preview');
  };

  const handleSignupStart = () => {
    setCurrentView('signup');
  };

  const handleBackToLanding = () => {
    setCurrentView('landing');
  };

  if (currentView === 'preview') {
    return (
      <div>
        <button
          onClick={handleBackToLanding}
          className="mb-4 text-indigo-600 hover:text-indigo-700 flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to overview
        </button>
        <QuickValuePreview
          onComplete={(role, challenge) => onGetStarted(role, challenge)}
        />
      </div>
    );
  }

  if (currentView === 'signup') {
    return (
      <div>
        <button
          onClick={handleBackToLanding}
          className="mb-4 text-indigo-600 hover:text-indigo-700 flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to overview
        </button>
        <StreamlinedRegister
          userRole={selectedRole}
          challenge={selectedChallenge}
          onSkip={handleBackToLanding}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-indigo-600">PsychSync</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-600 hover:text-gray-900">
                How it works
              </button>
              <button className="text-gray-600 hover:text-gray-900">
                Pricing
              </button>
              <button
                onClick={() => setCurrentView('signup')}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Sign up
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <div className="mb-8">
              <h2 className="text-5xl font-bold text-gray-900 mb-6">
                Understand Your Team.
                <br />
                <span className="text-indigo-600">Optimize Performance.</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
                PsychSync uses behavioral science and AI to analyze team dynamics,
                predict performance, and provide actionable insights that make your
                teams more effective and productive.
              </p>
            </div>

            {/* Interactive CTA */}
            <div className="mb-16">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                See how it works - try it now (no registration required)
              </h3>
              <button
                onClick={() => handlePreviewStart('', '')}
                className="bg-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition-colors shadow-lg"
              >
                <span className="mr-2">🚀</span>
                Try Free Team Analysis - 2 Minutes
              </button>
              <p className="text-sm text-gray-500 mt-3">
                Answer 2 questions → Get instant insights → No credit card needed
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Problems & Solutions */}
      <div className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Struggling with Team Challenges?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              PsychSync helps you solve the most common team problems with data-driven insights
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Problem 1 */}
            <div className="group">
              <div className="bg-red-50 rounded-lg p-6 group-hover:bg-red-100 transition-colors">
                <div className="flex items-center mb-4">
                  <div className="p-3 bg-red-100 rounded-lg mr-4">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Communication Breakdown</h3>
                </div>
                <p className="text-gray-700 mb-4">
                  Teams losing 2-3 hours weekly due to misunderstandings and communication gaps
                </p>
                <div className="flex items-center text-green-600 font-medium">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Reduce by 60% with PsychSync
                </div>
              </div>
            </div>

            {/* Problem 2 */}
            <div className="group">
              <div className="bg-blue-50 rounded-lg p-6 group-hover:bg-blue-100 transition-colors">
                <div className="flex items-center mb-4">
                  <div className="p-3 bg-blue-100 rounded-lg mr-4">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Low Productivity</h3>
                </div>
                <p className="text-gray-700 mb-4">
                  Teams operating at 60-70% capacity due to poor role alignment and motivation
                </p>
                <div className="flex items-center text-green-600 font-medium">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Increase by 25% with insights
                </div>
              </div>
            </div>

            {/* Problem 3 */}
            <div className="group">
              <div className="bg-purple-50 rounded-lg p-6 group-hover:bg-purple-100 transition-colors">
                <div className="flex items-center mb-4">
                  <div className="p-3 bg-purple-100 rounded-lg mr-4">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">High Turnover Risk</h3>
                </div>
                <p className="text-gray-700 mb-4">
                  Losing valuable team members costs 150% of their annual salary in replacement costs
                </p>
                <div className="flex items-center text-green-600 font-medium">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Reduce turnover by 40%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How PsychSync Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Get actionable team insights in three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <div className="text-center">
              <div className="bg-indigo-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-indigo-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Quick Assessment</h3>
              <p className="text-gray-600 mb-4">
                Team members complete a 2-minute personality assessment
                that reveals behavioral patterns and work preferences
              </p>
              <div className="bg-indigo-50 rounded-lg p-4">
                <p className="text-sm font-medium text-indigo-900">
                  📊 6 assessment frameworks available
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="bg-indigo-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-indigo-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">AI Analysis</h3>
              <p className="text-gray-600 mb-4">
                Our AI analyzes team dynamics, communication patterns, and
                behavioral compatibility to generate insights
              </p>
              <div className="bg-indigo-50 rounded-lg p-4">
                <p className="text-sm font-medium text-indigo-900">
                  🤖 Powered by behavioral science
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="bg-indigo-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-indigo-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Actionable Insights</h3>
              <p className="text-gray-600 mb-4">
                Get personalized recommendations to improve communication,
                productivity, and team satisfaction
              </p>
              <div className="bg-indigo-50 rounded-lg p-4">
                <p className="text-sm font-medium text-indigo-900">
                  🎯 Track measurable improvements
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Testimonials */}
      <div className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Trusted by 10,000+ Teams
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <img src="https://images.unsplash.com/photo-1494790108755-2616b332c5ca?w=40&h=40&fit=crop&crop=face"
                     alt="Sarah Chen" className="w-12 h-12 rounded-full mr-3" />
                <div>
                  <h4 className="font-semibold text-gray-900">Sarah Chen</h4>
                  <p className="text-sm text-gray-600">Engineering Manager, TechCorp</p>
                </div>
              </div>
              <p className="text-gray-700">
                "PsychSync helped us reduce team conflicts by 60% and improve our sprint velocity by 25%.
                The insights were spot-on and actionable from day one."
              </p>
              <div className="flex items-center mt-4">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <img src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face"
                     alt="Michael Rodriguez" className="w-12 h-12 rounded-full mr-3" />
                <div>
                  <h4 className="font-semibold text-gray-900">Michael Rodriguez</h4>
                  <p className="text-sm text-gray-600">HR Director, GlobalFinance</p>
                </div>
              </div>
              <p className="text-gray-700">
                "The behavioral insights helped us identify and address turnover risks before they became problems.
                We've saved over $200K in recruitment costs this year alone."
              </p>
              <div className="flex items-center mt-4">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=40&h=40&fit=crop&crop=face"
                     alt="Emily Johnson" className="w-12 h-12 rounded-full mr-3" />
                <div>
                  <h4 className="font-semibold text-gray-900">Emily Johnson</h4>
                  <p className="text-sm text-gray-600">Team Lead, StartupXYZ</p>
                </div>
              </div>
              <p className="text-gray-700">
                "Finally, a tool that actually helps me understand my team's dynamics.
                The recommendations are practical and have made a real difference in our daily standups."
              </p>
              <div className="flex items-center mt-4">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="py-20 bg-indigo-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Transform Your Team?
          </h2>
          <p className="text-xl text-indigo-100 mb-8">
            Join thousands of teams using PsychSync to unlock their full potential
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => handlePreviewStart('', '')}
              className="bg-white text-indigo-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Try Free Analysis - 2 Minutes
            </button>
            <button
              onClick={handleSignupStart}
              className="bg-indigo-500 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-400 transition-colors"
            >
              Sign Up Free
            </button>
          </div>
          <p className="text-sm text-indigo-100 mt-4">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </div>
    </div>
  );
};

export default ImprovedLanding;
