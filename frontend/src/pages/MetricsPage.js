import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Target, Clock, Zap, Brain, CheckCircle } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const PRIMARY_COLOR = '#3b82f6';
const SECONDARY_COLOR = '#7c3aed';
const PRIMARY_SOFT = '#3b82f6';
const SECONDARY_SOFT = '#7c3aed';
const ACCENT_INDIGO = '#4f46e5';
const CHART_GRID = '#e2e8f0';
const CHART_TEXT = '#64748b';

const MetricsPage = () => {
  const trainingData = [
    { epoch: 1, baseline_loss: 0.45, constraint_loss: 0.38, baseline_val: 0.52, constraint_val: 0.44 },
    { epoch: 2, baseline_loss: 0.35, constraint_loss: 0.28, baseline_val: 0.41, constraint_val: 0.32 },
    { epoch: 3, baseline_loss: 0.28, constraint_loss: 0.22, baseline_val: 0.35, constraint_val: 0.27 },
    { epoch: 4, baseline_loss: 0.24, constraint_loss: 0.18, baseline_val: 0.31, constraint_val: 0.23 },
    { epoch: 5, baseline_loss: 0.21, constraint_loss: 0.16, baseline_val: 0.28, constraint_val: 0.21 },
  ];

  const performanceMetrics = [
    {
      name: 'FID Score',
      baseline: 85.2,
      constraint: 57.4,
      improvement: -32.7,
      description: 'Fréchet Inception Distance - measures image quality',
      better: 'lower',
      unit: '',
    },
    {
      name: 'CLIP Score',
      baseline: 0.62,
      constraint: 0.75,
      improvement: 21.0,
      description: 'Text-image alignment quality',
      better: 'higher',
      unit: '',
    },
    {
      name: 'Adjacency Score',
      baseline: 0.41,
      constraint: 0.73,
      improvement: 78.0,
      description: 'Spatial relationship consistency',
      better: 'higher',
      unit: '',
    },
    {
      name: 'Overall Accuracy',
      baseline: 71.3,
      constraint: 84.5,
      improvement: 18.5,
      description: 'Combined generation quality metric',
      better: 'higher',
      unit: '%',
    },
  ];

  const radarData = [
    { metric: 'Quality', baseline: 65, constraint: 85, fullMark: 100 },
    { metric: 'Speed', baseline: 80, constraint: 75, fullMark: 100 },
    { metric: 'Consistency', baseline: 45, constraint: 80, fullMark: 100 },
    { metric: 'Accuracy', baseline: 71, constraint: 85, fullMark: 100 },
    { metric: 'Realism', baseline: 60, constraint: 82, fullMark: 100 },
  ];

  const generationStats = {
    totalGenerations: 15420,
    avgGenerationTime: 2.3,
    successRate: 94.2,
    userSatisfaction: 4.6,
  };

  const chartTooltip = {
    backgroundColor: 'rgba(15, 23, 42, 0.96)',
    border: '1px solid rgba(96, 165, 250, 0.18)',
    borderRadius: '16px',
    color: '#f8fafc',
    boxShadow: '0 18px 40px rgba(15, 23, 42, 0.2)',
  };

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-page-header">
          <h1 className="app-page-title mb-4">
            <span className="gradient-text">Performance</span> Metrics
          </h1>
          <p className="app-page-copy">
            Comprehensive analysis of model performance, training progress, and generation quality.
          </p>
        </motion.div>

        <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Total Generations', value: generationStats.totalGenerations.toLocaleString(), icon: Zap, change: '+12.5%' },
            { label: 'Avg Generation Time', value: `${generationStats.avgGenerationTime}s`, icon: Clock, change: '-0.3s' },
            { label: 'Success Rate', value: `${generationStats.successRate}%`, icon: Target, change: '+2.1%' },
            { label: 'User Rating', value: `${generationStats.userSatisfaction}/5`, icon: CheckCircle, change: '+0.2' },
          ].map((stat, index) => {
            const Icon = stat.icon;

            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="app-card app-card-hover metrics-highlight-card p-6"
              >
                <div className="mb-4 flex items-start justify-between gap-4">
                  <div className="app-icon-badge">
                    <Icon className="h-6 w-6" />
                  </div>
                  <span className="metrics-change-pill">
                    {stat.change}
                  </span>
                </div>
                <div className="metrics-highlight-value mb-1 text-2xl font-bold">{stat.value}</div>
                <div className="text-sm text-slate-600">{stat.label}</div>
              </motion.div>
            );
          })}
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card metrics-chart-card mb-8 p-8">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="app-section-title text-2xl">Training Progress</h2>
            <div className="flex gap-2">
              <button className="app-button-primary app-button-compact">Training Loss</button>
              <button className="app-button-secondary app-button-compact">Validation Loss</button>
            </div>
          </div>

          <div className="metrics-chart-frame">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trainingData} margin={{ top: 24, right: 28, left: 4, bottom: 12 }}>
                <defs>
                  <linearGradient id="trainingBaselineGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.72" />
                    <stop offset="100%" stopColor={PRIMARY_COLOR} />
                  </linearGradient>
                  <linearGradient id="trainingConstraintGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={PRIMARY_COLOR} />
                    <stop offset="100%" stopColor={SECONDARY_COLOR} />
                  </linearGradient>
                  <linearGradient id="trainingBaselineSoftGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={PRIMARY_SOFT} stopOpacity="0.42" />
                    <stop offset="100%" stopColor={PRIMARY_SOFT} stopOpacity="0.72" />
                  </linearGradient>
                  <linearGradient id="trainingConstraintSoftGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.42" />
                    <stop offset="100%" stopColor={SECONDARY_SOFT} stopOpacity="0.72" />
                  </linearGradient>
                  <filter id="trainingLineGlow" x="-35%" y="-35%" width="170%" height="170%">
                    <feDropShadow dx="0" dy="8" stdDeviation="7" floodColor={ACCENT_INDIGO} floodOpacity="0.28" />
                  </filter>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                <XAxis
                  dataKey="epoch"
                  stroke={CHART_TEXT}
                  tickLine={false}
                  axisLine={{ stroke: CHART_GRID }}
                  tickMargin={12}
                />
                <YAxis
                  stroke={CHART_TEXT}
                  tickLine={false}
                  axisLine={{ stroke: CHART_GRID }}
                  tickMargin={10}
                  width={42}
                />
                <Tooltip contentStyle={chartTooltip} cursor={{ stroke: 'rgba(99, 102, 241, 0.18)', strokeWidth: 2 }} />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: 18 }} />
                <Line
                  type="monotone"
                  dataKey="baseline_loss"
                  stroke="url(#trainingBaselineGradient)"
                  strokeWidth={3}
                  name="Baseline Training"
                  dot={{ fill: '#ffffff', stroke: PRIMARY_COLOR, strokeWidth: 2, r: 4 }}
                  activeDot={{ fill: PRIMARY_COLOR, stroke: '#ffffff', strokeWidth: 2, r: 7 }}
                  filter="url(#trainingLineGlow)"
                  isAnimationActive
                  animationBegin={120}
                  animationDuration={1200}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="constraint_loss"
                  stroke="url(#trainingConstraintGradient)"
                  strokeWidth={3}
                  name="Constraint-Aware Training"
                  dot={{ fill: '#ffffff', stroke: SECONDARY_COLOR, strokeWidth: 2, r: 4 }}
                  activeDot={{ fill: SECONDARY_COLOR, stroke: '#ffffff', strokeWidth: 2, r: 7 }}
                  filter="url(#trainingLineGlow)"
                  isAnimationActive
                  animationBegin={220}
                  animationDuration={1300}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="baseline_val"
                  stroke="url(#trainingBaselineSoftGradient)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Baseline Validation"
                  dot={{ fill: '#ffffff', stroke: PRIMARY_SOFT, strokeWidth: 2, r: 3 }}
                  isAnimationActive
                  animationBegin={320}
                  animationDuration={1100}
                  animationEasing="ease-out"
                />
                <Line
                  type="monotone"
                  dataKey="constraint_val"
                  stroke="url(#trainingConstraintSoftGradient)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Constraint-Aware Validation"
                  dot={{ fill: '#ffffff', stroke: SECONDARY_SOFT, strokeWidth: 2, r: 3 }}
                  isAnimationActive
                  animationBegin={420}
                  animationDuration={1100}
                  animationEasing="ease-out"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="app-card metrics-chart-card p-8">
            <h2 className="app-section-title mb-6 text-2xl">Performance Comparison</h2>
            <div className="metrics-chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={performanceMetrics}
                  margin={{ top: 24, right: 24, left: 8, bottom: 18 }}
                  barCategoryGap="24%"
                  barGap={8}
                >
                  <defs>
                    <linearGradient id="barBaselineGradient" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.58" />
                      <stop offset="100%" stopColor={PRIMARY_COLOR} />
                    </linearGradient>
                    <linearGradient id="barConstraintGradient" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} />
                      <stop offset="100%" stopColor={SECONDARY_COLOR} />
                    </linearGradient>
                    <filter id="barGlow" x="-30%" y="-30%" width="160%" height="170%">
                      <feDropShadow dx="0" dy="10" stdDeviation="8" floodColor={SECONDARY_COLOR} floodOpacity="0.26" />
                    </filter>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke={CHART_TEXT}
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tickLine={false}
                    axisLine={{ stroke: CHART_GRID }}
                    tickMargin={14}
                  />
                  <YAxis
                    stroke={CHART_TEXT}
                    tickLine={false}
                    axisLine={{ stroke: CHART_GRID }}
                    tickMargin={10}
                    width={42}
                  />
                  <Tooltip contentStyle={chartTooltip} cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }} />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: 12 }} />
                  <Bar
                    dataKey="baseline"
                    fill="url(#barBaselineGradient)"
                    name="Baseline Model"
                    radius={[16, 16, 0, 0]}
                    maxBarSize={48}
                    isAnimationActive
                    animationBegin={140}
                    animationDuration={1000}
                    animationEasing="ease-out"
                  />
                  <Bar
                    dataKey="constraint"
                    fill="url(#barConstraintGradient)"
                    name="Constraint-Aware"
                    radius={[16, 16, 0, 0]}
                    maxBarSize={48}
                    filter="url(#barGlow)"
                    isAnimationActive
                    animationBegin={260}
                    animationDuration={1150}
                    animationEasing="ease-out"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="app-card metrics-chart-card p-8">
            <h2 className="app-section-title mb-6 text-2xl">Model Capabilities</h2>
            <div className="metrics-chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} margin={{ top: 24, right: 36, bottom: 24, left: 36 }}>
                  <defs>
                    <linearGradient id="radarBaselineStroke" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.7" />
                      <stop offset="100%" stopColor={PRIMARY_COLOR} />
                    </linearGradient>
                    <linearGradient id="radarConstraintStroke" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} />
                      <stop offset="100%" stopColor={SECONDARY_COLOR} />
                    </linearGradient>
                    <linearGradient id="radarBaselineFill" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.18" />
                      <stop offset="100%" stopColor={PRIMARY_COLOR} stopOpacity="0.05" />
                    </linearGradient>
                    <linearGradient id="radarConstraintFill" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor={PRIMARY_COLOR} stopOpacity="0.14" />
                      <stop offset="100%" stopColor={SECONDARY_COLOR} stopOpacity="0.2" />
                    </linearGradient>
                    <filter id="radarGlow" x="-30%" y="-30%" width="160%" height="160%">
                      <feDropShadow dx="0" dy="10" stdDeviation="9" floodColor={ACCENT_INDIGO} floodOpacity="0.24" />
                    </filter>
                  </defs>
                  <PolarGrid stroke={CHART_GRID} />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: CHART_TEXT }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Radar
                    name="Baseline Model"
                    dataKey="baseline"
                    stroke="url(#radarBaselineStroke)"
                    fill="url(#radarBaselineFill)"
                    fillOpacity={1}
                    strokeWidth={2}
                    isAnimationActive
                    animationBegin={160}
                    animationDuration={1000}
                    animationEasing="ease-out"
                  />
                  <Radar
                    name="Constraint-Aware"
                    dataKey="constraint"
                    stroke="url(#radarConstraintStroke)"
                    fill="url(#radarConstraintFill)"
                    fillOpacity={1}
                    strokeWidth={2}
                    filter="url(#radarGlow)"
                    isAnimationActive
                    animationBegin={280}
                    animationDuration={1150}
                    animationEasing="ease-out"
                  />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: 12 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card p-8">
          <h2 className="app-section-title mb-6 text-2xl">Detailed Performance Analysis</h2>
          <div className="app-table-wrap">
            <table className="w-full">
              <thead>
                <tr className="border-b border-primary-100">
                  <th className="px-4 py-4 text-left font-semibold text-slate-950">Metric</th>
                  <th className="px-4 py-4 text-center font-semibold text-slate-950">Baseline</th>
                  <th className="px-4 py-4 text-center font-semibold text-slate-950">Constraint-Aware</th>
                  <th className="px-4 py-4 text-center font-semibold text-slate-950">Improvement</th>
                  <th className="px-4 py-4 text-left font-semibold text-slate-950">Description</th>
                </tr>
              </thead>
              <tbody>
                {performanceMetrics.map((metric) => {
                  const isPositiveImprovement = metric.better === 'lower'
                    ? metric.improvement < 0
                    : metric.improvement > 0;

                  return (
                    <tr key={metric.name} className="border-b border-slate-100 transition-colors hover:bg-primary-50/40">
                      <td className="px-4 py-4 font-medium text-slate-950">{metric.name}</td>
                      <td className="px-4 py-4 text-center text-slate-600">
                        {metric.baseline}{metric.unit}
                      </td>
                      <td className="px-4 py-4 text-center font-semibold text-primary-700">
                        {metric.constraint}{metric.unit}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`metrics-improvement-badge ${isPositiveImprovement ? '' : 'metrics-improvement-badge-negative'}`}>
                          {metric.improvement > 0 ? '+' : ''}{metric.improvement.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-slate-600">{metric.description}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card-muted mt-8 p-8">
          <h2 className="app-section-title mb-6 text-center text-2xl">Key Insights</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="app-card app-card-hover metrics-insight-card metrics-insight-card-accent p-6 text-center">
              <div className="app-icon-badge-lg mx-auto mb-4">
                <TrendingUp className="h-8 w-8" />
              </div>
              <h3 className="mb-2 font-semibold text-slate-950">Significant Improvement</h3>
              <p className="text-sm text-slate-600">
                Constraint-aware model shows 18.5% accuracy improvement over baseline.
              </p>
            </div>
            <div className="app-card app-card-hover metrics-insight-card p-6 text-center">
              <div className="app-icon-badge-lg mx-auto mb-4">
                <Brain className="h-8 w-8" />
              </div>
              <h3 className="mb-2 font-semibold text-slate-950">Spatial Understanding</h3>
              <p className="text-sm text-slate-600">
                78% improvement in adjacency consistency demonstrates better spatial reasoning.
              </p>
            </div>
            <div className="app-card app-card-hover metrics-insight-card p-6 text-center">
              <div className="app-icon-badge-lg mx-auto mb-4">
                <BarChart3 className="h-8 w-8" />
              </div>
              <h3 className="mb-2 font-semibold text-slate-950">Production Ready</h3>
              <p className="text-sm text-slate-600">
                94.2% success rate and 4.6/5 user satisfaction indicate production readiness.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default MetricsPage;
