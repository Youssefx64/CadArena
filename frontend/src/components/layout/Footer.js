import React from 'react';
import { Github, Linkedin, Mail, Heart } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  const brandMarkSrc = `${process.env.PUBLIC_URL}/studio-app/assets/cadarena-mark.svg`;

  const socialLinks = [
    { name: 'GitHub Repo', icon: Github, href: 'https://github.com/Youssefx64/CadArena' },
    { name: 'LinkedIn', icon: Linkedin, href: 'https://www.linkedin.com/in/yousseftahaai/' },
    { name: 'Email', icon: Mail, href: 'mailto:cadarena.ai@gmail.com' },
  ];

  const footerLinks = [
    {
      title: 'Product',
      links: [
        { name: 'Studio', href: '/studio' },
        { name: 'Generate', href: '/generate' },
        { name: 'Models', href: '/models' },
        { name: 'Metrics', href: '/metrics' },
      ],
    },
    {
      title: 'Project',
      links: [
        { name: 'About', href: '/about' },
        { name: 'Developer', href: '/developers' },
        { name: 'GitHub Repo', href: 'https://github.com/Youssefx64/CadArena' },
        { name: 'LinkedIn', href: 'https://www.linkedin.com/in/yousseftahaai/' },
      ],
    },
    {
      title: 'Resources',
      links: [
        { name: 'Project Email', href: 'mailto:cadarena.ai@gmail.com' },
        { name: 'API Docs', href: '/docs' },
        { name: 'Repository Issues', href: 'https://github.com/Youssefx64/CadArena/issues' },
        { name: 'Home', href: '/' },
      ],
    },
  ];

  return (
    <footer className="app-footer">
      <div className="app-shell relative py-14">
        <div className="app-footer-grid">
          <div className="app-footer-brand">
            <div className="mb-5 flex items-center gap-4">
              <img
                src={brandMarkSrc}
                alt="CadArena"
                className="app-footer-logo"
              />
              <div className="flex flex-col leading-none">
                <span className="text-xl font-bold text-white">CadArena</span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-400">
                  AI Layout Workspace
                </span>
              </div>
            </div>
            <p className="app-footer-copy">
              Conversational CAD studio built by Youssef Taha Badawi for turning natural-language intent
              into architectural layouts, DXF exports, and AI-assisted design workflows.
            </p>
            <div className="app-footer-socials">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="app-footer-social-link"
                    aria-label={social.name}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {footerLinks.map((section) => (
            <div key={section.title} className="app-footer-section">
              <h3 className="app-footer-heading">
                {section.title}
              </h3>
              <ul className="space-y-3.5">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      className="app-footer-link"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="app-footer-bottom">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex flex-wrap items-center justify-center gap-1 text-sm text-slate-400 md:justify-start">
              <span>© {currentYear} CadArena. Built with</span>
              <Heart className="w-4 h-4 text-secondary-400" />
              <span>for practical architectural AI workflows.</span>
            </div>
            <div className="flex gap-6">
              <a href="mailto:cadarena.ai@gmail.com" className="app-footer-meta-link">
                Contact
              </a>
              <a href="https://www.linkedin.com/in/yousseftahaai/" className="app-footer-meta-link">
                LinkedIn
              </a>
              <a href="https://github.com/Youssefx64/CadArena" className="app-footer-meta-link">
                Repository
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
