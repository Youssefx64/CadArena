import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Target, Clock, Zap, Brain, CheckCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const MetricsPage = () => {
  const [selectedMetric, setSelectedMetric] = useState('accuracy');
  const [timeRange, setTimeRange] = useState('all');

  // Mock training data
  const trainingData = [
    { epoch: 1, baseline_loss: 0.45, constraint_loss: 0.38, baseline_val: 0.52, constraint_val: 0.44 },
    { epoch: 2, baseline_loss: 0.35, constraint_loss: 0.28, baseline_val: 0.41, constraint_val: 0.32 },
    { epoch: 3, baseline_loss: 0.28, constraint_loss: 0.22, baseline_val: 0.35, constraint_val: 0.27 },
    { epoch: 4, baseline_loss: 0.24, constraint_loss: 0.18, baseline_val: 0.31, constraint_val: 0.23 },
    { epoch: 5, baseline_loss: 0.21, constraint_loss: 0.16, baseline_val: 0.28, constraint_val: 0.21 }
  ];

  const performanceMetrics = [
    {
      name: 'FID Score',
      baseline: 85.2,
      constraint: 57.4,
      improvement: -32.7,
      description: 'Fréchet Inception Distance - measures image quality',
      better: 'lower',
      unit: ''
    },
    {
      name: 'CLIP Score',
      baseline: 0.62,
      constraint: 0.75,
      improvement: 21.0,
      description: 'Text-image alignment quality',
      better: 'higher',
      unit: ''
    },
    {
      name: 'Adjacency Score',
      baseline: 0.41,
      constraint: 0.73,
      improvement: 78.0,
      description: 'Spatial relationship consistency',
      better: 'higher',
      unit: ''
    },
    {
      name: 'Overall Accuracy',
      baseline: 71.3,
      constraint: 84.5,
      improvement: 18.5,
      description: 'Combined generation quality metric',
      better: 'higher',
      unit: '%'
    }
  ];

  const radarData = [
    {
      metric: 'Quality',
      baseline: 65,
      constraint: 85,
      fullMark: 100
    },
    {
      metric: 'Speed',
      baseline: 80,
      constraint: 75,
      fullMark: 100
    },
    {
      metric: 'Consistency',
      baseline: 45,
      constraint: 80,
      fullMark: 100
    },
    {
      metric: 'Accuracy',
      baseline: 71,
      constraint: 85,
      fullMark: 100
    },
    {
      metric: 'Realism',
      baseline: 60,
      constraint: 82,
      fullMark: 100
    }
  ];

  const generationStats = {
    totalGenerations: 15420,
    avgGenerationTime: 2.3,
    successRate: 94.2,
    userSatisfaction: 4.6
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            <span className="gradient-text">Performance</span> Metrics
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive analysis of model performance, training progress, and generation quality
          </p>
        </motion.div>

        {/* Key Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {[
            { 
              label: 'Total Generations', 
              value: generationStats.totalGenerations.toLocaleString(), 
              icon: Zap, 
              color: 'blue',
              change: '+12.5%'
            },
            { 
              label: 'Avg Generation Time', 
              value: `${generationStats.avgGenerationTime}s`, 
              icon: Clock, 
              color: 'green',
              change: '-0.3s'
            },
            { 
              label: 'Success Rate', 
              value: `${generationStats.successRate}%`, 
              icon: Target, 
              color: 'purple',
              change: '+2.1%'
            },
            { 
              label: 'User Rating', 
              value: `${generationStats.userSatisfaction}/5`, 
              icon: CheckCircle, 
              color: 'orange',
              change: '+0.2'
            }
          ].map((stat, index) => {
            const Icon = stat.icon;
            const colorClasses = {
              blue: 'from-blue-500 to-cyan-500',
              green: 'from-green-500 to-emerald-500',
              purple: 'from-purple-500 to-pink-500',
              orange: 'from-orange-500 to-red-500'
            };
            
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${colorClasses[stat.color]} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                    {stat.change}
                  </span>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            );
          })}
        </div>

        {/* Training Progress Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Training Progress</h2>
            <div className="flex space-x-2">
              <button className="px-4 py-2 bg-primary-100 text-primary-700 rounded-lg text-sm font-medium">
                Training Loss
              </button>
              <button className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium">
                Validation Loss
              </button>
            </div>
          </div>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trainingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="epoch" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#f9fafb'
                  }} 
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="baseline_loss" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  name="Baseline Training"
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="constraint_loss" 
                  stroke="#8b5cf6" 
                  strokeWidth={3}
                  name="Constraint-Aware Training"
                  dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="baseline_val" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Baseline Validation"
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="constraint_val" 
                  stroke="#8b5cf6" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Constraint-Aware Validation"
                  dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Performance Metrics Bar Chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance Comparison</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={performanceMetrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="name" 
                    stroke="#6b7280"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#6b7280" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1f2937', 
                      border: 'none', 
                      borderRadius: '8px',
                      color: '#f9fafb'
                    }} 
                  />
                  <Legend />
                  <Bar dataKey="baseline" fill="#3b82f6" name="Baseline Model" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="constraint" fill="#8b5cf6" name="Constraint-Aware" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Radar Chart */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Model Capabilities</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <PolarRadiusAxis 
                    angle={90} 
                    domain={[0, 100]} 
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                  />
                  <Radar
                    name="Baseline Model"
                    dataKey="baseline"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.1}
                    strokeWidth={2}
                  />
                  <Radar
                    name="Constraint-Aware"
                    dataKey="constraint"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>

        {/* Detailed Metrics Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Performance Analysis</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">Metric</th>
                  <th className="text-center py-4 px-4 font-semibold text-gray-900">Baseline</th>
                  <th className="text-center py-4 px-4 font-semibold text-gray-900">Constraint-Aware</th>
                  <th className="text-center py-4 px-4 font-semibold text-gray-900">Improvement</th>
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">Description</th>
                </tr>
              </thead>
              <tbody>
                {performanceMetrics.map((metric, index) => (
                  <tr key={metric.name} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-4 px-4 font-medium text-gray-900">{metric.name}</td>
                    <td className="py-4 px-4 text-center text-gray-600">
                      {metric.baseline}{metric.unit}
                    </td>
                    <td className="py-4 px-4 text-center font-semibold text-primary-600">
                      {metric.constraint}{metric.unit}
                    </td>
                    <td className="py-4 px-4 text-center">
                      <span className={`font-semibold ${
                        metric.improvement > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {metric.improvement > 0 ? '+' : ''}{metric.improvement.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-4 px-4 text-sm text-gray-600">{metric.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Key Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-gradient-to-r from-primary-50 to-secondary-50 rounded-2xl p-8"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Key Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Significant Improvement</h3>
              <p className="text-sm text-gray-600">
                Constraint-aware model shows 18.5% accuracy improvement over baseline
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Spatial Understanding</h3>
              <p className="text-sm text-gray-600">
                78% improvement in adjacency consistency demonstrates better spatial reasoning
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Production Ready</h3>
              <p className="text-sm text-gray-600">
                94.2% success rate and 4.6/5 user satisfaction indicate production readiness
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default MetricsPage;