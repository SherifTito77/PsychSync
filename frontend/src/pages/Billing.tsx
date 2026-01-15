// src/pages/Billing.tsx
// Billing history and subscription management page
import React, { useState, useEffect, memo } from 'react';
import { Link } from 'react-router-dom';
import { useSubscription } from '../contexts/SubscriptionContext';
import { SubscriptionTier } from '../types/subscription';
import UsageDashboard from '../components/subscription/UsageDashboard';
import CancelFlow from '../components/subscription/CancelFlow';
import UpgradePrompt from '../components/subscription/UpgradePrompt';

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  description: string;
  downloadUrl?: string;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'bank';
  last4: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  isDefault: boolean;
}

const Billing: React.FC = () => {
  const { subscription } = useSubscription();
  const [showCancelFlow, setShowCancelFlow] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'history' | 'payment'>('overview');

  // Mock billing data
  const invoices: Invoice[] = [
    {
      id: 'inv-2025-01',
      date: '2025-01-15',
      amount: 29.00,
      status: 'paid',
      description: 'Premium Plan - Monthly',
      downloadUrl: '/invoices/inv-2025-01.pdf',
    },
    {
      id: 'inv-2024-12',
      date: '2024-12-15',
      amount: 29.00,
      status: 'paid',
      description: 'Premium Plan - Monthly',
      downloadUrl: '/invoices/inv-2024-12.pdf',
    },
    {
      id: 'inv-2024-11',
      date: '2024-11-15',
      amount: 290.00,
      status: 'paid',
      description: 'Premium Plan - Annual',
      downloadUrl: '/invoices/inv-2024-11.pdf',
    },
  ];

  const paymentMethods: PaymentMethod[] = [
    {
      id: 'pm-1',
      type: 'card',
      last4: '4242',
      brand: 'Visa',
      expiryMonth: 12,
      expiryYear: 2026,
      isDefault: true,
    },
  ];

  const statusColors = {
    paid: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
  };

  if (!subscription) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Active Subscription</h2>
          <p className="text-gray-600 mb-6">You don't have an active subscription yet.</p>
          <Link
            to="/pricing"
            className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
          >
            View Pricing Plans
          </Link>
        </div>
      </div>
    );
  }

  if (showCancelFlow) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <button
          onClick={() => setShowCancelFlow(false)}
          className="text-gray-600 hover:text-gray-900 mb-6"
        >
          ← Back to Billing
        </button>
        <CancelFlow
          onCancelComplete={() => {
            setShowCancelFlow(false);
            // Redirect or show confirmation
          }}
          onOfferAccepted={(offerId) => {
            setShowCancelFlow(false);
            // Handle offer acceptance
          }}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
        <p className="text-gray-600 mt-1">Manage your subscription, payment methods, and billing history</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'history'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Billing History
          </button>
          <button
            onClick={() => setActiveTab('payment')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'payment'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Payment Methods
          </button>
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Current Plan */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-6 text-white">
            <div className="flex items-start justify-between">
              <div>
                <span className="inline-block px-3 py-1 bg-white bg-opacity-20 rounded-full text-sm font-semibold mb-4">
                  Current Plan
                </span>
                <h2 className="text-3xl font-bold mb-2">
                  {subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)}
                </h2>
                <p className="text-indigo-100 mb-4">
                  {subscription.billingInterval.charAt(0).toUpperCase() + subscription.billingInterval.slice(1)} billing •
                  Renews on {new Date(subscription.nextBillingDate).toLocaleDateString()}
                </p>
                <div className="flex items-center gap-4 text-sm">
                  <span>${subscription.tier === SubscriptionTier.PREMIUM ? '29.00' : subscription.tier === SubscriptionTier.ENTERPRISE ? '99.00' : '0.00'}/month</span>
                  {subscription.tier !== SubscriptionTier.ENTERPRISE && (
                    <Link
                      to="/pricing"
                      className="underline hover:no-underline"
                    >
                      View all plans →
                    </Link>
                  )}
                </div>
              </div>
              {subscription.tier === SubscriptionTier.FREE && (
                <Link
                  to="/pricing"
                  className="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-indigo-50 transition-colors"
                >
                  Upgrade Now
                </Link>
              )}
            </div>
          </div>

          {/* Usage Dashboard */}
          <UsageDashboard />

          {/* Quick Actions */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                to="/pricing"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">Upgrade Plan</h4>
                  <p className="text-sm text-gray-600">Get access to more features</p>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>

              <button
                onClick={() => setShowCancelFlow(true)}
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50 transition-colors text-left w-full"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">Cancel Subscription</h4>
                  <p className="text-sm text-gray-600">Stop future billing</p>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>

              <a
                href="mailto:support@psychsync.com"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">Contact Support</h4>
                  <p className="text-sm text-gray-600">Get help with billing</p>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </a>

              <Link
                to="/settings"
                className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">Account Settings</h4>
                  <p className="text-sm text-gray-600">Update your preferences</p>
                </div>
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Billing History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Billing History</h3>
              <p className="text-sm text-gray-600">View and download your past invoices</p>
            </div>
            <div className="divide-y divide-gray-200">
              {invoices.map((invoice) => (
                <div key={invoice.id} className="p-6 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-medium text-gray-900">{invoice.description}</span>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${statusColors[invoice.status]}`}>
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {new Date(invoice.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-semibold text-gray-900">
                      ${invoice.amount.toFixed(2)}
                    </span>
                    {invoice.downloadUrl && (
                      <button
                        onClick={() => console.log('Download invoice:', invoice.id)}
                        className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                      >
                        Download PDF
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tax Information */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Tax Information</h3>
            <div className="text-sm text-gray-600 space-y-2">
              <p>All charges are in USD. Tax is calculated based on your billing location.</p>
              <p>VAT ID: <span className="font-medium text-gray-900">US123456789</span> (add your VAT ID in settings)</p>
            </div>
          </div>
        </div>
      )}

      {/* Payment Methods Tab */}
      {activeTab === 'payment' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Payment Methods</h3>
                  <p className="text-sm text-gray-600">Manage your payment options</p>
                </div>
                <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors">
                  Add Payment Method
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {paymentMethods.map((method) => (
                <div key={method.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">{method.brand || 'CARD'}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {method.brand} ending in {method.last4}
                      </p>
                      {method.type === 'card' && method.expiryMonth && method.expiryYear && (
                        <p className="text-sm text-gray-600">
                          Expires {method.expiryMonth}/{method.expiryYear}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {method.isDefault && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                        Default
                      </span>
                    )}
                    <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Billing Address */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Billing Address</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p>Your billing address is used to calculate tax and appears on your invoices.</p>
              <button className="text-indigo-600 hover:text-indigo-700 font-medium">
                + Add billing address
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

Billing.displayName = 'Billing';

export default Billing;
