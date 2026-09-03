/**
 * Product Operations Page
 *
 * Wrapper page for the Product Operations Dashboard
 * NOTE: DashboardLayout is provided by the route in App.tsx, not here
 */

import React from 'react';
import ProductOperationsDashboard from '../components/ProductOperationsDashboard';

const ProductOperationsPage: React.FC = () => {
  return (
    <div className="min-h-screen">
      <ProductOperationsDashboard />
    </div>
  );
};

export default ProductOperationsPage;
