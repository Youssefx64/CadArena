import React from 'react';
import { Brain } from 'lucide-react';
import ComingSoon from '../components/ComingSoon';

const ModelsPage = () => (
  <ComingSoon
    icon={Brain}
    title="AI Model Browser"
    subtitle="An interactive model dashboard is in development. You can read full model documentation — including architecture details, training process, and benchmark results — in the Docs page."
    features={[
      'Interactive model comparison table with all benchmark metrics',
      'Downloadable model weights with version history',
      'Architecture diagrams for baseline and constraint-aware models',
      'Live benchmark runner: test a prompt against both models side by side',
      'Training visualizations: loss curves, validation metrics, epoch-by-epoch progress',
      'Fine-tune API: submit your own dataset and request a custom fine-tune',
    ]}
    ctaLabel="Read Model Docs"
    ctaTo="/docs#models"
    secondaryLabel="About the Project"
    secondaryTo="/about"
  />
);

export default ModelsPage;
