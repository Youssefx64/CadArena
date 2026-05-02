import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Github, Linkedin, Mail, ExternalLink, Code2, Award, Heart, BookOpen } from 'lucide-react';
import developersData from '../data/developers.json';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.09 } } };
const fadeUp  = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } } };

const dev = developersData.developers[0];

const DevelopersPage = () => (
  <div className="app-page">
    <div className="app-shell">

      {/* ── Header ── */}
      <motion.div initial="hidden" animate="visible" variants={stagger} className="app-page-header mb-16">
        <motion.div variants={fadeUp} className="mb-5">
          <span className="app-pill">
            <Code2 className="h-4 w-4" aria-hidden="true" />
            {developersData.team.version} · {developersData.team.license}
          </span>
        </motion.div>
        <motion.h1 variants={fadeUp} className="app-page-title mb-4">
          Meet the <span className="gradient-text">Builder</span>
        </motion.h1>
        <motion.p variants={fadeUp} className="app-page-copy">
          {developersData.team.description}
        </motion.p>
        <motion.div variants={fadeUp} className="mt-6 flex flex-wrap justify-center gap-3">
          <a href={developersData.team.repository} target="_blank" rel="noopener noreferrer"
            className="app-button-secondary app-button-compact">
            <Github className="h-4 w-4" aria-hidden="true" />
            View Repository
            <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </motion.div>
      </motion.div>

      {/* ── Stats strip ── */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
        className="mb-16 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {Object.entries(developersData.statistics).map(([key, value]) => (
          <motion.div key={key} variants={fadeUp}
            className="app-card app-card-hover p-5 text-center">
            <p className="mb-1 text-2xl font-black text-primary-700 sm:text-3xl">{value}</p>
            <p className="text-xs font-semibold capitalize text-slate-500">{key.replace(/_/g, ' ')}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Developer card ── */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
        <motion.h2 variants={fadeUp} className="app-section-title mb-10 text-center">Project Owner</motion.h2>

        <motion.div variants={fadeUp} className="mx-auto max-w-2xl">
          <div className="app-card app-card-hover p-8">
            {/* Top section */}
            <div className="mb-8 flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-6 sm:text-left">
              <img
                src={dev.avatar}
                alt={dev.name}
                className="h-24 w-24 flex-shrink-0 rounded-full border-4 border-primary-100 object-cover shadow-lg"
              />
              <div className="text-center sm:text-left">
                <h3 className="mb-1 text-xl font-black text-slate-950">{dev.name}</h3>
                <p className="mb-3 font-semibold text-primary-700">{dev.role}</p>
                <p className="text-sm leading-relaxed text-slate-600">{dev.bio}</p>
              </div>
            </div>

            {/* Contributions */}
            <div className="mb-8">
              <h4 className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-slate-400">
                <Award className="h-4 w-4" aria-hidden="true" />
                Key Contributions
              </h4>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {dev.contributions.map((c) => (
                  <li key={c} className="flex items-start gap-2.5 text-sm text-slate-700">
                    <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-500" aria-hidden="true" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>

            {/* Social links */}
            <div className="flex flex-wrap justify-center gap-3 border-t border-slate-100 pt-6">
              {dev.links.github && (
                <a href={dev.links.github} target="_blank" rel="noopener noreferrer"
                  className="app-button-secondary app-button-compact">
                  <Github className="h-4 w-4" aria-hidden="true" />
                  GitHub
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              )}
              {dev.links.linkedin && (
                <a href={dev.links.linkedin} target="_blank" rel="noopener noreferrer"
                  className="app-button-secondary app-button-compact">
                  <Linkedin className="h-4 w-4" aria-hidden="true" />
                  LinkedIn
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              )}
              {dev.links.email && (
                <a href={`mailto:${dev.links.email}`}
                  className="app-button-secondary app-button-compact">
                  <Mail className="h-4 w-4" aria-hidden="true" />
                  {dev.links.email}
                </a>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* ── Tech stack ── */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
        <motion.h2 variants={fadeUp} className="app-section-title mb-10 text-center">
          <Code2 className="mr-2 inline-block h-7 w-7 align-middle text-primary-600" aria-hidden="true" />
          Technology Stack
        </motion.h2>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {developersData.technologies.map((tech) => (
            <motion.div key={tech.category} variants={fadeUp} className="app-card p-6">
              <h3 className="app-card-title mb-4">{tech.category}</h3>
              <ul className="space-y-2">
                {tech.items.map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-slate-600">
                    <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-500" aria-hidden="true" />
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* ── Acknowledgments ── */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
        <motion.h2 variants={fadeUp} className="app-section-title mb-10 text-center">
          <Heart className="mr-2 inline-block h-6 w-6 align-middle text-secondary-500" aria-hidden="true" />
          Acknowledgments
        </motion.h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {developersData.acknowledgments.map((ack) => (
            <motion.a key={ack.name} variants={fadeUp}
              href={ack.link} target="_blank" rel="noopener noreferrer"
              className="app-card app-card-hover group p-6">
              <h3 className="mb-2 flex items-center justify-between font-semibold text-slate-950 transition-colors group-hover:text-primary-700">
                {ack.name}
                <ExternalLink className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" aria-hidden="true" />
              </h3>
              <p className="text-sm text-slate-600">{ack.contribution}</p>
            </motion.a>
          ))}
        </div>
      </motion.div>

      {/* ── CTA ── */}
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
        className="app-cta-panel p-12 text-center">
        <motion.h2 variants={fadeUp} className="app-section-title mb-4 text-white">
          Explore CadArena
        </motion.h2>
        <motion.p variants={fadeUp} className="mx-auto mb-8 max-w-xl text-lg text-primary-100">
          CadArena is designed and maintained by {dev.name}. Explore the repository,
          read the docs, or connect directly.
        </motion.p>
        <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-3">
          <a href={developersData.team.repository} target="_blank" rel="noopener noreferrer"
            className="app-button-secondary">
            <Github className="h-5 w-5" aria-hidden="true" />
            Repository
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
          <Link to="/docs" className="app-button-secondary">
            <BookOpen className="h-5 w-5" aria-hidden="true" />
            Documentation
          </Link>
          <a href={`mailto:${dev.links.email}`} className="app-button-ghost">
            <Mail className="h-5 w-5" aria-hidden="true" />
            Get in touch
          </a>
        </motion.div>
      </motion.div>

    </div>
  </div>
);

export default DevelopersPage;
