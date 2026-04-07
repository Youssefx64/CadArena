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
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <img
                src={brandMarkSrc}
                alt="CadArena"
                className="w-11 h-11 rounded-xl shadow-lg shadow-cyan-950/20 ring-1 ring-cyan-200/20"
              />
              <div className="flex flex-col leading-none">
                <span className="text-xl font-bold text-white">CadArena</span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.28em] text-gray-400">
                  AI Layout Workspace
                </span>
              </div>
            </div>
            <p className="text-gray-400 mb-6 max-w-md">
              Conversational CAD studio built by Youssef Taha Badawi for turning natural-language intent
              into architectural layouts, DXF exports, and AI-assisted design workflows.
            </p>
            <div className="flex space-x-4">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800"
                    aria-label={social.name}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Links Sections */}
          {footerLinks.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
                {section.title}
              </h3>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.href}
                      className="text-gray-400 hover:text-white transition-colors text-sm"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-800 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-1 text-sm text-gray-400">
              <span>© {currentYear} CadArena. Built with</span>
              <Heart className="w-4 h-4 text-red-500" />
              <span>for practical architectural AI workflows.</span>
            </div>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="mailto:cadarena.ai@gmail.com" className="text-sm text-gray-400 hover:text-white transition-colors">
                Contact
              </a>
              <a href="https://www.linkedin.com/in/yousseftahaai/" className="text-sm text-gray-400 hover:text-white transition-colors">
                LinkedIn
              </a>
              <a href="https://github.com/Youssefx64/CadArena" className="text-sm text-gray-400 hover:text-white transition-colors">
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
