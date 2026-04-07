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
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5 }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="text-center mb-16"
        >
          <motion.div variants={itemVariants} className="mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-2xl mb-4">
              <Users className="w-10 h-10 text-white" />
            </div>
          </motion.div>
          
          <motion.h1 
            variants={itemVariants}
            className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4"
          >
            Meet the <span className="gradient-text">Builder</span>
          </motion.h1>
          
          <motion.p 
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto mb-6"
          >
            {developersData.team.description}
          </motion.p>

          <motion.div 
            variants={itemVariants}
            className="flex flex-wrap justify-center gap-4 text-sm text-gray-600"
          >
            <span className="px-4 py-2 bg-white rounded-full shadow-sm">
              Version {developersData.team.version}
            </span>
            <span className="px-4 py-2 bg-white rounded-full shadow-sm">
              {developersData.team.license} License
            </span>
            <a 
              href={developersData.team.repository}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-white rounded-full shadow-sm hover:shadow-md transition-shadow flex items-center gap-2"
            >
              <Github className="w-4 h-4" />
              View Repository
            </a>
          </motion.div>
        </motion.div>

        {/* Project Statistics */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-16"
        >
          {Object.entries(developersData.statistics).map(([key, value]) => (
            <motion.div
              key={key}
              variants={itemVariants}
              className="bg-white rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-2xl sm:text-3xl font-bold text-primary-600 mb-2">
                {value}
              </div>
              <div className="text-xs sm:text-sm text-gray-600 capitalize">
                {key.replace(/_/g, ' ')}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Developers Grid */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-3xl font-bold text-gray-900 mb-8 text-center"
          >
            Project Owner
          </motion.h2>
          
          <div className="grid grid-cols-1 max-w-xl mx-auto gap-8">
            {developersData.developers.map((dev) => (
              <motion.div
                key={dev.id}
                variants={itemVariants}
                className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 card-hover"
              >
                {/* Avatar */}
                <div className="flex flex-col items-center mb-6">
                  <img
                    src={dev.avatar}
                    alt={dev.name}
                    className="w-24 h-24 rounded-full mb-4 ring-4 ring-primary-100"
                  />
                  <h3 className="text-xl font-bold text-gray-900">{dev.name}</h3>
                  <p className="text-sm text-primary-600 font-medium">{dev.role}</p>
                </div>

                {/* Bio */}
                <p className="text-gray-600 text-sm mb-6 text-center">
                  {dev.bio}
                </p>

                {/* Contributions */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                    <Award className="w-4 h-4 mr-2 text-primary-500" />
                    Key Contributions
                  </h4>
                  <ul className="space-y-2">
                    {dev.contributions.map((contribution, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-primary-500 mr-2">•</span>
                        <span>{contribution}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Social Links */}
                <div className="flex justify-center gap-3 pt-4 border-t border-gray-100">
                  {dev.links.github && (
                    <a
                      href={dev.links.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="GitHub"
                    >
                      <Github className="w-5 h-5" />
                    </a>
                  )}
                  {dev.links.linkedin && (
                    <a
                      href={dev.links.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="LinkedIn"
                    >
                      <Linkedin className="w-5 h-5" />
                    </a>
                  )}
                  {dev.links.email && (
                    <a
                      href={`mailto:${dev.links.email}`}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="Email"
                    >
                      <Mail className="w-5 h-5" />
                    </a>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Technologies */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-3xl font-bold text-gray-900 mb-8 text-center"
          >
            <Code className="w-8 h-8 inline-block mr-2 text-primary-600" />
            Technology Stack
          </motion.h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {developersData.technologies.map((tech, idx) => (
              <motion.div
                key={idx}
                variants={itemVariants}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {tech.category}
                </h3>
                <ul className="space-y-2">
                  {tech.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="text-sm text-gray-600 flex items-center">
                      <span className="w-2 h-2 bg-primary-500 rounded-full mr-2"></span>
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Acknowledgments */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="mb-16"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-3xl font-bold text-gray-900 mb-8 text-center"
          >
            <Heart className="w-8 h-8 inline-block mr-2 text-red-500" />
            Acknowledgments
          </motion.h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {developersData.acknowledgments.map((ack, idx) => (
              <motion.a
                key={idx}
                href={ack.link}
                target="_blank"
                rel="noopener noreferrer"
                variants={itemVariants}
                className="bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 card-hover group"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors flex items-center justify-between">
                  {ack.name}
                  <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </h3>
                <p className="text-sm text-gray-600">{ack.contribution}</p>
              </motion.a>
            ))}
          </div>
        </motion.div>

        {/* Footer CTA */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={containerVariants}
          className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-3xl p-12 text-center text-white"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-3xl font-bold mb-4"
          >
            Explore CadArena
          </motion.h2>
          <motion.p 
            variants={itemVariants}
            className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto"
          >
            CadArena is designed and maintained by {leadDeveloper.name}. Explore the repository or connect directly for collaboration.
          </motion.p>
          <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={developersData.team.repository}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-8 py-4 bg-white text-primary-600 font-semibold rounded-xl hover:bg-gray-50 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <Github className="w-5 h-5 mr-2" />
              View Repository
              <ExternalLink className="w-4 h-4 ml-2" />
            </a>
            <a
              href={leadDeveloper.links.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-8 py-4 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all duration-200 border-2 border-white/30"
            >
              Connect on LinkedIn
              <ExternalLink className="w-4 h-4 ml-2" />
            </a>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default DevelopersPage;
