import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap, Brain, BarChart3, Sparkles, CheckCircle, Play } from 'lucide-react';
import { motion } from 'framer-motion';

const HomePage = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Generation',
      description: 'Advanced diffusion models fine-tuned on architectural datasets for precise floor plan generation.',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Zap,
      title: 'Constraint-Aware Design',
      description: 'Ensures spatial consistency and adjacency relationships for realistic architectural layouts.',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: BarChart3,
      title: 'Performance Metrics',
      description: 'Comprehensive evaluation using FID, CLIP-Score, and adjacency consistency metrics.',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: Sparkles,
      title: 'Real-time Generation',
      description: 'Fast inference with optimized models for quick floor plan generation from text prompts.',
      color: 'from-orange-500 to-red-500'
    }
  ];

  const stats = [
    { label: 'Accuracy Improvement', value: '+13.2%', description: 'Over baseline models' },
    { label: 'FID Score', value: '57.4', description: 'Industry-leading quality' },
    { label: 'CLIP Score', value: '0.75', description: 'Text-image alignment' },
    { label: 'Generation Time', value: '2.3s', description: 'Average processing time' }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-20 sm:py-32">
        {/* Animated Background Elements */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-primary-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-secondary-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" style={{animationDelay: '2s'}}></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-accent-200 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" style={{animationDelay: '4s'}}></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
            className="text-center"
          >
            <motion.div variants={itemVariants} className="mb-8">
              <motion.span 
                className="inline-flex items-center px-6 py-3 rounded-full text-sm font-medium bg-gradient-to-r from-primary-100 to-secondary-100 text-primary-800 mb-6 border border-primary-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI-Powered Architecture • Live Demo Available
              </motion.span>
            </motion.div>
            
            <motion.h1 
              variants={itemVariants}
              className="text-4xl sm:text-6xl lg:text-7xl font-bold text-gray-900 mb-6"
            >
              <motion.span 
                className="gradient-text inline-block"
                animate={{ 
                  backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
                }}
                transition={{ 
                  duration: 5, 
                  repeat: Infinity, 
                  ease: "linear" 
                }}
              >
                CadArena
              </motion.span>
              <br />
              <span className="text-gray-700">Conversational CAD Studio</span>
            </motion.h1>
            
            <motion.p 
              variants={itemVariants}
              className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed"
            >
              Transform natural language descriptions into structured architectural layouts,
              DXF-ready outputs, and scalable AI-assisted CAD workflows.
            </motion.p>
            
            <motion.div 
              variants={itemVariants}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  to="/studio"
                  className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-primary-600 to-secondary-600 text-white font-semibold rounded-xl hover:from-primary-700 hover:to-secondary-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Try Generator
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Link>
              </motion.div>
              
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  to="/models"
                  className="inline-flex items-center px-8 py-4 bg-white text-gray-700 font-semibold rounded-xl border-2 border-gray-200 hover:border-primary-300 hover:text-primary-700 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  <Play className="w-5 h-5 mr-2" />
                  View Models
                </Link>
              </motion.div>
            </motion.div>

            {/* Live Demo Preview */}
            <motion.div
              variants={itemVariants}
              className="mt-16"
            >
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-lg border border-gray-200 max-w-4xl mx-auto">
                <div className="flex items-center justify-center space-x-4 mb-6">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <span className="text-sm font-medium text-gray-600">CadArena Studio</span>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-left">
                  <div className="text-sm text-gray-500 mb-2">Input:</div>
                  <div className="font-mono text-sm text-gray-800 mb-4">
                    "3-bedroom apartment with open kitchen and living room"
                  </div>
                  <div className="text-sm text-gray-500 mb-2">Output:</div>
                  <div className="bg-gradient-to-r from-primary-100 to-secondary-100 rounded-lg p-6 text-center">
                    <div className="text-4xl mb-2">🏠</div>
                    <div className="text-sm text-gray-600">Generated Floor Plan</div>
                    <div className="text-xs text-primary-600 mt-1">84.5% Accuracy • 2.3s Generation Time</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="grid grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                variants={itemVariants}
                className="text-center"
              >
                <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-sm font-semibold text-gray-900 mb-1">
                  {stat.label}
                </div>
                <div className="text-xs text-gray-500">
                  {stat.description}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="text-center mb-16"
          >
            <motion.h2 
              variants={itemVariants}
              className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4"
            >
              Powerful AI Features
            </motion.h2>
            <motion.p 
              variants={itemVariants}
              className="text-xl text-gray-600 max-w-3xl mx-auto"
            >
              Built with cutting-edge machine learning techniques and architectural expertise
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  variants={itemVariants}
                  className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition-all duration-300 card-hover"
                >
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-6`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Model Comparison Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="text-center mb-16"
          >
            <motion.h2 
              variants={itemVariants}
              className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4"
            >
              Model Performance
            </motion.h2>
            <motion.p 
              variants={itemVariants}
              className="text-xl text-gray-600 max-w-3xl mx-auto"
            >
              Constraint-aware diffusion significantly outperforms baseline models
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-3xl p-8 lg:p-12"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <motion.div variants={itemVariants}>
                <h3 className="text-2xl font-bold text-gray-900 mb-6">
                  Key Improvements
                </h3>
                <div className="space-y-4">
                  {[
                    { metric: 'FID Score Improvement', value: '-27.8 points', description: 'Better image quality' },
                    { metric: 'CLIP Score Improvement', value: '+0.13 points', description: 'Better text alignment' },
                    { metric: 'Adjacency Consistency', value: '+0.32 points', description: 'Spatial relationships' },
                    { metric: 'Overall Accuracy', value: '+13.2%', description: 'Generation quality' }
                  ].map((item, index) => (
                    <div key={item.metric} className="flex items-center space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-gray-900">{item.metric}</span>
                          <span className="font-bold text-primary-600">{item.value}</span>
                        </div>
                        <p className="text-sm text-gray-600">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="text-center">
                <div className="bg-white rounded-2xl p-8 shadow-lg">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    Constraint-Aware Model
                  </h4>
                  <div className="text-4xl font-bold text-primary-600 mb-2">84.5%</div>
                  <div className="text-sm text-gray-600 mb-4">Overall Accuracy</div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full" style={{width: '84.5%'}}></div>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-primary-600 to-secondary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
          >
            <motion.h2 
              variants={itemVariants}
              className="text-3xl lg:text-4xl font-bold text-white mb-4"
            >
              Ready to Generate Floor Plans?
            </motion.h2>
            <motion.p 
              variants={itemVariants}
              className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto"
            >
              Experience CadArena's conversational CAD workflow for moving from intent
              to architectural layouts and exportable design artifacts.
            </motion.p>
            <motion.div variants={itemVariants}>
              <Link
                to="/studio"
                className="inline-flex items-center px-8 py-4 bg-white text-primary-600 font-semibold rounded-xl hover:bg-gray-50 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                <Zap className="w-5 h-5 mr-2" />
                Start Generating
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
