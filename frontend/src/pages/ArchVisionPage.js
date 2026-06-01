import React from 'react';
import { Zap } from 'lucide-react';
import ComingSoon from '../components/ComingSoon';

const ArchVisionPage = () => (
  <ComingSoon
    icon={Zap}
    title="ArchVision is Coming Soon"
    subtitle="Transform architectural concepts into stunning photorealistic renders or artistic sketches in seconds. We're putting the finishing touches on this experience."
    features={[
      'AI-powered architectural visualization from text prompts',
      'Multiple style presets: Modern, Minimalist, Brutalist, Neo-Gothic, and more',
      'Adjustable creativity and aspect ratio controls',
      'Download and share your generated renders',
    ]}
    ctaLabel="Open CAD Studio"
    ctaTo="/studio"
    secondaryLabel="Back to Home"
    secondaryTo="/"
  />
);

export default ArchVisionPage;
