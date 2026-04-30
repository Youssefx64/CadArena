import React from 'react';
import { Award, Star, Shield, Zap } from 'lucide-react';

const badgeConfig = {
  first_question: {
    icon: Star,
    label: 'First Question',
    color: 'bg-blue-100 text-blue-700',
    tooltip: 'Asked their first question',
  },
  first_answer: {
    icon: Star,
    label: 'First Answer',
    color: 'bg-green-100 text-green-700',
    tooltip: 'Provided their first answer',
  },
  helpful: {
    icon: Award,
    label: 'Helpful',
    color: 'bg-amber-100 text-amber-700',
    tooltip: '10+ helpful votes',
  },
  expert: {
    icon: Zap,
    label: 'Expert',
    color: 'bg-purple-100 text-purple-700',
    tooltip: 'High reputation contributor',
  },
  moderator: {
    icon: Shield,
    label: 'Moderator',
    color: 'bg-red-100 text-red-700',
    tooltip: 'Community moderator',
  },
};

export default function UserBadge({ badge, size = 'sm' }) {
  if (!badge || !badgeConfig[badge]) return null;

  const config = badgeConfig[badge];
  const Icon = config.icon;
  const sizeClass = size === 'lg' ? 'h-5 w-5' : 'h-4 w-4';

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${config.color}`}
      title={config.tooltip}
    >
      <Icon className={sizeClass} />
      <span>{config.label}</span>
    </div>
  );
}
