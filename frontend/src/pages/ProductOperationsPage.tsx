/**
 * Product Operations Page
 *
 * Wrapper page for the Product Operations Dashboard
 * Provides layout and integration with the main app
 */

import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import ProductOperationsDashboard from '../components/ProductOperationsDashboard';

const ProductOperationsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <DashboardLayout>
      <div className="min-h-screen">
        <ProductOperationsDashboard />
      </div>
    </DashboardLayout>
  );
};

export default ProductOperationsPage;
