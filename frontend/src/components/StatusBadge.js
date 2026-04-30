import React from 'react';
import { CheckCircle2, AlertCircle, TrendingUp } from 'lucide-react';

const statusConfig = {
  answered: {
    icon: CheckCircle2,
    label: 'Answered',
    color: 'bg-green-50 text-green-700 border-green-200',
  },
  unanswered: {
    icon: AlertCircle,
    label: 'Unanswered',
    color: 'bg-red-50 text-red-700 border-red-200',
  },
  trending: {
    icon: TrendingUp,
    label: 'Trending',
    color: 'bg-orange-50 text-orange-700 border-orange-200',
  },
};

export default function StatusBadge({ status }) {
  if (!status || !statusConfig[status]) return null;

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold ${config.color}`}>
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </span>
  );
}
