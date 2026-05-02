import React from 'react';
import { BarChart3 } from 'lucide-react';
import ComingSoon from '../components/ComingSoon';

const MetricsPage = () => (
  <ComingSoon
    icon={BarChart3}
    title="Live Performance Dashboard"
    subtitle="The metrics dashboard is being connected to live generation telemetry. Benchmark results and model comparisons are already available in the About and Docs pages."
    features={[
      'Real-time generation counters, success rates, and average latency',
      'Model comparison charts: FID, CLIP-Score, and adjacency metrics per version',
      'Training history: full loss curves and validation plots across all epochs',
      'Radar chart: multi-dimensional model capability comparison',
      'Per-prompt analytics: quality scores and constraint satisfaction breakdown',
      'Export metrics as CSV or JSON for offline analysis',
    ]}
    ctaLabel="See Current Results"
    ctaTo="/about"
    secondaryLabel="Read Model Docs"
    secondaryTo="/docs#models"
  />
);

export default MetricsPage;
