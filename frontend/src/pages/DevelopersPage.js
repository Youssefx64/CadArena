import React from 'react';
import { motion } from 'framer-motion';
import { Github, Linkedin, Mail, ExternalLink, Code, Users, Award, Heart } from 'lucide-react';
import developersData from '../data/developers.json';

const DevelopersPage = () => {
  const leadDeveloper = developersData.developers[0];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5 },
    },
  };

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div initial="hidden" animate="visible" variants={containerVariants} className="app-page-header">
          <motion.div variants={itemVariants} className="mb-6">
            <div className="app-icon-badge-lg mx-auto">
              <Users className="h-10 w-10 text-white" />
            </div>
          </motion.div>

          <motion.h1 variants={itemVariants} className="app-page-title mb-4">
            Meet the <span className="gradient-text">Builder</span>
          </motion.h1>

          <motion.p variants={itemVariants} className="app-page-copy mb-6">
            {developersData.team.description}
          </motion.p>

          <motion.div variants={itemVariants} className="flex flex-wrap justify-center gap-4 text-sm text-slate-600">
            <span className="app-pill-muted">Version {developersData.team.version}</span>
            <span className="app-pill-muted">{developersData.team.license} License</span>
            <a
              href={developersData.team.repository}
              target="_blank"
              rel="noopener noreferrer"
              className="app-button-secondary app-button-compact"
            >
              <Github className="h-4 w-4" />
              View Repository
            </a>
          </motion.div>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16 grid grid-cols-2 gap-4 md:grid-cols-5"
        >
          {Object.entries(developersData.statistics).map(([key, value]) => (
            <motion.div key={key} variants={itemVariants} className="app-card app-card-hover p-6 text-center">
              <div className="mb-2 text-2xl font-bold text-primary-700 sm:text-3xl">{value}</div>
              <div className="text-xs capitalize text-slate-600 sm:text-sm">
                {key.replace(/_/g, ' ')}
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 variants={itemVariants} className="app-section-title mb-8 text-center">
            Project Owner
          </motion.h2>

          <div className="mx-auto grid max-w-xl grid-cols-1 gap-8">
            {developersData.developers.map((dev) => (
              <motion.div key={dev.id} variants={itemVariants} className="app-card app-card-hover p-8">
                <div className="mb-6 flex flex-col items-center">
                  <img
                    src={dev.avatar}
                    alt={dev.name}
                    className="mb-4 h-24 w-24 rounded-full border-4 border-primary-100 object-cover shadow-soft"
                  />
                  <h3 className="text-xl font-bold text-slate-950">{dev.name}</h3>
                  <p className="text-sm font-medium text-primary-700">{dev.role}</p>
                </div>

                <p className="mb-6 text-center text-sm text-slate-600">{dev.bio}</p>

                <div className="mb-6">
                  <h4 className="mb-3 flex items-center text-sm font-semibold text-slate-950">
                    <Award className="mr-2 h-4 w-4 text-primary-600" />
                    Key Contributions
                  </h4>
                  <ul className="space-y-2">
                    {dev.contributions.map((contribution) => (
                      <li key={contribution} className="flex items-start text-sm text-slate-600">
                        <span className="mr-2 text-primary-600">•</span>
                        <span>{contribution}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex justify-center gap-3 border-t border-primary-100 pt-4">
                  {dev.links.github && (
                    <a
                      href={dev.links.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-full border border-primary-100 bg-primary-50 p-3 text-slate-600 transition-colors hover:text-primary-700"
                      title="GitHub"
                    >
                      <Github className="h-5 w-5" />
                    </a>
                  )}
                  {dev.links.linkedin && (
                    <a
                      href={dev.links.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-full border border-primary-100 bg-primary-50 p-3 text-slate-600 transition-colors hover:text-primary-700"
                      title="LinkedIn"
                    >
                      <Linkedin className="h-5 w-5" />
                    </a>
                  )}
                  {dev.links.email && (
                    <a
                      href={`mailto:${dev.links.email}`}
                      className="rounded-full border border-primary-100 bg-primary-50 p-3 text-slate-600 transition-colors hover:text-primary-700"
                      title="Email"
                    >
                      <Mail className="h-5 w-5" />
                    </a>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 variants={itemVariants} className="app-section-title mb-8 text-center">
            <Code className="mr-2 inline-block h-8 w-8 text-primary-600" />
            Technology Stack
          </motion.h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {developersData.technologies.map((tech, idx) => (
              <motion.div key={idx} variants={itemVariants} className="app-card app-card-hover p-6">
                <h3 className="app-card-title mb-4">{tech.category}</h3>
                <ul className="space-y-2">
                  {tech.items.map((item) => (
                    <li key={item} className="flex items-center text-sm text-slate-600">
                      <span className="mr-2 h-2 w-2 rounded-full bg-primary-600" />
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 variants={itemVariants} className="app-section-title mb-8 text-center">
            <Heart className="mr-2 inline-block h-8 w-8 text-secondary-500" />
            Acknowledgments
          </motion.h2>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {developersData.acknowledgments.map((ack, idx) => (
              <motion.a
                key={idx}
                href={ack.link}
                target="_blank"
                rel="noopener noreferrer"
                variants={itemVariants}
                className="app-card app-card-hover group p-6"
              >
                <h3 className="mb-2 flex items-center justify-between text-lg font-semibold text-slate-950 transition-colors group-hover:text-primary-700">
                  {ack.name}
                  <ExternalLink className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
                </h3>
                <p className="text-sm text-slate-600">{ack.contribution}</p>
              </motion.a>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="app-cta-panel p-12 text-center"
        >
          <motion.h2 variants={itemVariants} className="app-section-title mb-4 text-white">
            Explore CadArena
          </motion.h2>
          <motion.p variants={itemVariants} className="mx-auto mb-8 max-w-2xl text-xl text-primary-100">
            CadArena is designed and maintained by {leadDeveloper.name}. Explore the repository or connect directly for collaboration.
          </motion.p>
          <motion.div variants={itemVariants} className="flex flex-col justify-center gap-4 sm:flex-row">
            <a
              href={developersData.team.repository}
              target="_blank"
              rel="noopener noreferrer"
              className="app-button-secondary"
            >
              <Github className="h-5 w-5" />
              View Repository
              <ExternalLink className="h-4 w-4" />
            </a>
            <a
              href={leadDeveloper.links.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="app-button-secondary"
            >
              Connect on LinkedIn
              <ExternalLink className="ml-2 inline h-4 w-4" />
            </a>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default DevelopersPage;
