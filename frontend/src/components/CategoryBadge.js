import React from 'react';

const categoryColors = {
  architecture: 'bg-blue-50 text-blue-700 border-blue-200',
  civil: 'bg-green-50 text-green-700 border-green-200',
  structural: 'bg-purple-50 text-purple-700 border-purple-200',
  construction: 'bg-orange-50 text-orange-700 border-orange-200',
  mep: 'bg-red-50 text-red-700 border-red-200',
  materials: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  surveying: 'bg-indigo-50 text-indigo-700 border-indigo-200',
};

export default function CategoryBadge({ category, showCount = false, count = 0 }) {
  const color = categoryColors[category] || 'bg-slate-50 text-slate-700 border-slate-200';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold ${color}`}>
      <div className="h-2 w-2 rounded-full bg-current opacity-60" />
      {category.charAt(0).toUpperCase() + category.slice(1)}
      {showCount && <span className="ml-1 opacity-70">({count})</span>}
    </span>
  );
}
