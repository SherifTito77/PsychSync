/**
 * ScreeningRouter — maps /screening/:toolId to the correct clinical screening component.
 *
 * Each component is lazy-loaded so only the requested tool's bundle is fetched.
 * Unknown toolIds redirect back to the /screening overview.
 */

import { lazy, Suspense } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { ClinicalConsentWrapper } from '../components/clinical/ClinicalConsentWrapper';

const TOOL_MAP: Record<string, React.LazyExoticComponent<React.ComponentType<any>>> = {
  phq9: lazy(() => import('../components/clinical/PHQ9Screening')),
  gad7: lazy(() => import('../components/clinical/GAD7Screening')),
  cssrs: lazy(() => import('../components/clinical/CSSRSScreening')),
  'crisis-resources': lazy(() => import('../components/clinical/CrisisResources')),
  lsas: lazy(() => import('../components/clinical/LSASScreening')),
  eat26: lazy(() => import('../components/clinical/EAT26Screening')),
  ybocs: lazy(() => import('../components/clinical/YBOCSScreening')),
  bdi2: lazy(() => import('../components/clinical/BDI2Screening')),
  bai: lazy(() => import('../components/clinical/BAIScreening')),
  dass21: lazy(() => import('../components/clinical/DASS21Screening')),
  pcl5: lazy(() => import('../components/clinical/PCL5Screening')),
  audit: lazy(() => import('../components/clinical/AUDITScreening')),
  pss10: lazy(() => import('../components/clinical/PSS10Screening')),
  isi: lazy(() => import('../components/clinical/ISIScreening')),
  cbi: lazy(() => import('../components/clinical/CBIScreening')),
  mdq: lazy(() => import('../components/clinical/MDQScreening')),
  dast10: lazy(() => import('../components/clinical/DAST10Screening')),
  aq10: lazy(() => import('../components/clinical/AQ10Screening')),
  ace: lazy(() => import('../components/clinical/ACEScreening')),
  iesr: lazy(() => import('../components/clinical/IESRScreening')),
  iat: lazy(() => import('../components/clinical/IATScreening')),
  asrs: lazy(() => import('../components/clinical/ASRSScreening')),
};

// Tools that skip the consent gate (e.g. emergency resources)
const SKIP_CONSENT = new Set(['crisis-resources']);

export default function ScreeningRouter() {
  const { toolId } = useParams<{ toolId: string }>();

  const Component = toolId ? TOOL_MAP[toolId] : null;

  if (!Component) {
    return <Navigate to="/screening" replace />;
  }

  const content = (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-gray-500">Loading screening tool...</div>
        </div>
      }
    >
      <Component />
    </Suspense>
  );

  if (SKIP_CONSENT.has(toolId!)) {
    return content;
  }

  return (
    <ClinicalConsentWrapper screeningType={toolId!}>
      {content}
    </ClinicalConsentWrapper>
  );
}
