import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, Target, Code, Lightbulb, Rocket, ArrowRight } from 'lucide-react';

const AboutPage = () => {
  const features = [
    {
      icon: Brain,
      title: 'Advanced AI Models',
      description: 'State-of-the-art diffusion models fine-tuned specifically for architectural floor plan generation with spatial constraint awareness.',
    },
    {
      icon: Zap,
      title: 'Real-time Generation',
      description: 'Fast inference pipeline optimized for quick floor plan generation from natural language descriptions in under 3 seconds.',
    },
    {
      icon: Target,
      title: 'High Accuracy',
      description: '84.5% generation accuracy with comprehensive evaluation metrics including FID, CLIP-Score, and adjacency consistency.',
    },
    {
      icon: Code,
      title: 'Open Architecture',
      description: 'Modular, extensible codebase built with modern technologies and best practices for easy integration and customization.',
    },
  ];

  const achievements = [
    {
      category: 'AI Innovation',
      title: 'Advanced Diffusion Models',
      description: 'Developed state-of-the-art constraint-aware diffusion models with 84.5% accuracy.',
      icon: Brain,
      metrics: ['84.5% Accuracy', '57.4 FID Score', '0.75 CLIP Score'],
    },
    {
      category: 'Technical Excellence',
      title: 'Production-Ready Architecture',
      description: 'Built scalable, modular system with comprehensive API and responsive frontend.',
      icon: Code,
      metrics: ['React + FastAPI', 'RESTful API', 'Responsive Design'],
    },
    {
      category: 'Performance',
      title: 'Industry-Leading Results',
      description: 'Achieved significant improvements over baseline models across all evaluation metrics.',
      icon: Target,
      metrics: ['+32.7% FID', '+78% Adjacency', '+18.5% Overall'],
    },
    {
      category: 'User Experience',
      title: 'Intuitive Interface',
      description: 'Designed user-friendly interface for seamless conversational CAD workflows.',
      icon: Lightbulb,
      metrics: ['2.3s Generation', '94.2% Success Rate', '4.6/5 Rating'],
    },
  ];

  const team = [
    {
      name: 'Youssef Taha Badawi',
      role: 'Founder, AI Engineer & Systems Architect',
      description: 'AI Engineer | GenAI Solutions Developer | LLM Systems Engineer | Conversational CAD Systems Engineer | Architecting Agentic & RAG Systems | Building Scalable AI That Solves Real Problems.',
      icon: Brain,
    },
  ];

  const stats = [
    { label: 'Model Accuracy', value: '84.5%' },
    { label: 'Generation Speed', value: '2.3s' },
    { label: 'Training Epochs', value: '5' },
    { label: 'Dataset Size', value: '1K+' },
  ];

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-page-header">
          <h1 className="app-page-title mb-6">
            About <span className="gradient-text">CadArena</span>
          </h1>
          <p className="app-page-copy max-w-4xl">
            CadArena is an AI-powered conversational CAD platform that transforms natural-language intent
            into structured architectural layouts, DXF exports, and practical design workflows.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="app-cta-panel mb-16 p-12 text-center"
        >
          <h2 className="app-section-title mb-6 text-white">Our Mission</h2>
          <p className="mx-auto max-w-4xl text-xl leading-8 text-primary-100">
            To make architectural AI genuinely useful in practice by combining conversational interfaces,
            reliable CAD outputs, and scalable systems that help designers move faster from intent to execution.
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-16">
          <h2 className="app-section-title mb-12 text-center">Key Features</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="app-card app-card-hover p-8"
                >
                  <div className="app-icon-badge-lg mb-6">
                    <Icon className="h-8 w-8" />
                  </div>
                  <h3 className="app-card-title mb-4">{feature.title}</h3>
                  <p className="app-body">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card mb-16 p-12">
          <h2 className="app-section-title mb-12 text-center">By the Numbers</h2>
          <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="mb-2 text-4xl font-bold text-primary-700 lg:text-5xl">{stat.value}</div>
                <div className="font-medium text-slate-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-16">
          <h2 className="app-section-title mb-12 text-center">Key Achievements</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {achievements.map((achievement, index) => {
              const Icon = achievement.icon;
              return (
                <motion.div
                  key={achievement.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="app-card app-card-hover group p-8"
                >
                  <div className="mb-6 flex items-start gap-4">
                    <div className="app-icon-badge-lg transition-transform duration-300 group-hover:scale-105">
                      <Icon className="h-8 w-8" />
                    </div>
                    <div className="flex-1">
                      <div className="mb-1 text-sm font-semibold text-primary-700">{achievement.category}</div>
                      <h3 className="app-card-title mb-2">{achievement.title}</h3>
                    </div>
                  </div>

                  <p className="mb-6 text-slate-600">{achievement.description}</p>

                  <div className="flex flex-wrap gap-2">
                    {achievement.metrics.map((metric) => (
                      <span key={metric} className="app-pill-muted">
                        {metric}
                      </span>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-16">
          <h2 className="app-section-title mb-12 text-center">Project Leadership</h2>
          <div className="mx-auto grid max-w-3xl grid-cols-1 gap-6">
            {team.map((member, index) => {
              const Icon = member.icon;
              return (
                <motion.div
                  key={member.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="app-card app-card-hover p-6 text-center"
                >
                  <div className="app-icon-badge-lg mx-auto mb-4">
                    <Icon className="h-8 w-8" />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-slate-950">{member.name}</h3>
                  <div className="mb-3 font-medium text-primary-700">{member.role}</div>
                  <p className="text-sm text-slate-600">{member.description}</p>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-16">
          <h2 className="app-section-title mb-12 text-center">Technology Stack</h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {[
              {
                title: 'AI & Machine Learning',
                icon: '🧠',
                technologies: [
                  { name: 'PyTorch & Diffusers', desc: 'Deep learning framework' },
                  { name: 'Stable Diffusion 2.1', desc: 'Foundation model' },
                  { name: 'CLIP & Transformers', desc: 'Text understanding' },
                  { name: 'Custom Constraints', desc: 'Spatial awareness' },
                ],
              },
              {
                title: 'Backend & API',
                icon: '⚙️',
                technologies: [
                  { name: 'FastAPI & Python', desc: 'Backend application layer' },
                  { name: 'RESTful APIs', desc: 'Workspace, auth, and export flows' },
                  { name: 'DXF Export Pipeline', desc: 'CAD generation and preview delivery' },
                  { name: 'Persistence Layer', desc: 'Project and profile storage' },
                ],
              },
              {
                title: 'Frontend & UI',
                icon: '🎨',
                technologies: [
                  { name: 'React 18', desc: 'Modern UI framework' },
                  { name: 'Tailwind CSS', desc: 'Utility-first styling' },
                  { name: 'Framer Motion', desc: 'Smooth animations' },
                  { name: 'Responsive Design', desc: 'Mobile-first approach' },
                ],
              },
            ].map((stack, index) => (
              <motion.div
                key={stack.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="app-card app-card-hover p-8"
              >
                <div className="mb-6 flex items-center gap-4">
                  <div className="app-icon-badge text-2xl">{stack.icon}</div>
                  <h3 className="app-card-title">{stack.title}</h3>
                </div>
                <div className="space-y-4">
                  {stack.technologies.map((tech) => (
                    <div key={tech.name} className="flex items-start gap-3">
                      <div className="mt-2 h-2 w-2 rounded-full bg-primary-600" />
                      <div>
                        <div className="font-medium text-slate-950">{tech.name}</div>
                        <div className="text-sm text-slate-600">{tech.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="app-cta-panel relative overflow-hidden p-12">
            <div className="absolute inset-0 bg-slate-950/10" />
            <div className="relative z-10">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                className="mx-auto mb-8 h-20 w-20"
              >
                <Rocket className="h-20 w-20 text-white" />
              </motion.div>
              <h2 className="app-section-title mb-6 text-white">The Future of Conversational CAD</h2>
              <p className="mx-auto mb-12 max-w-4xl text-xl leading-8 text-primary-100">
                CadArena is being shaped as a practical foundation for agentic design workflows, structured
                architectural reasoning, and CAD systems that solve real-world problems instead of stopping at demos.
              </p>

              <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
                {[
                  { icon: '🏗️', title: '3D Generation', desc: 'Full 3D architectural models' },
                  { icon: '🥽', title: 'VR Integration', desc: 'Immersive design experience' },
                  { icon: '🤝', title: 'Collaboration', desc: 'Real-time team design' },
                  { icon: '📱', title: 'Mobile Apps', desc: 'Design on the go' },
                ].map((feature, index) => (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="rounded-2xl border border-white/15 bg-white/12 p-6 backdrop-blur-md transition-all duration-300 hover:bg-white/18"
                  >
                    <div className="mb-3 text-3xl">{feature.icon}</div>
                    <h3 className="mb-2 font-semibold text-white">{feature.title}</h3>
                    <p className="text-sm text-primary-100">{feature.desc}</p>
                  </motion.div>
                ))}
              </div>

              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1 }}
                className="inline-flex"
              >
                <div className="app-button-secondary cursor-pointer">
                  <span>Built for Real-World AI Workflows</span>
                  <ArrowRight className="h-5 w-5" />
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AboutPage;
