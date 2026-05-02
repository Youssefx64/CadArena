import React from 'react';
import { Zap } from 'lucide-react';
import ComingSoon from '../components/ComingSoon';

const GeneratorPage = () => (
  <ComingSoon
    icon={Zap}
    title="AI Floor Plan Generator"
    subtitle="The standalone generator page is being rebuilt with a faster, more interactive interface. In the meantime, use the full Studio workspace to generate and refine floor plans conversationally."
    features={[
      'Real-time text-to-floor-plan generation with live progress indicator',
      'Side-by-side prompt history and plan comparison view',
      'One-click DXF export with AutoCAD layer mapping',
      'Preset library: apartment, villa, office, studio, and more',
      'Constraint editor: set minimum room sizes, adjacency rules, and EBC compliance flags',
      'Generation settings: model selection, style presets, resolution, and seed control',
    ]}
    ctaLabel="Open Studio"
    ctaTo="/studio"
    secondaryLabel="Read the Docs"
    secondaryTo="/docs"
  />
);

export default GeneratorPage;
