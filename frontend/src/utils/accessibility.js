/**
 * SEO and Accessibility utilities for CadArena
 * Handles meta tags, structured data, accessibility features
 */

/**
 * Meta tags configuration for different pages
 */
export const META_TAGS = {
  default: {
    title: 'CadArena - AI-Powered Architectural CAD Studio',
    description: 'Transform natural language into professional architectural floor plans using AI. Generate DXF-ready layouts with constraint-aware design.',
    keywords: 'floor plan, architecture, CAD, AI, design, layout, DXF, conversational',
    ogImage: '/og-image.png',
    ogType: 'website',
    twitterCard: 'summary_large_image',
  },
  home: {
    title: 'CadArena - Conversational CAD Studio',
    description: 'Generate professional floor plans from natural language descriptions. AI-powered architecture design made simple.',
  },
  studio: {
    title: 'CadArena Studio - Floor Plan Generator',
    description: 'Create, edit, and export architectural floor plans with AI assistance.',
    robots: 'noindex, nofollow', // Studio is dynamic content
  },
  models: {
    title: 'CadArena Models - AI Architecture Models',
    description: 'Explore our fine-tuned diffusion models for floor plan generation.',
  },
  metrics: {
    title: 'CadArena Metrics - Performance & Benchmarks',
    description: 'View detailed performance metrics and benchmarks for our architecture AI.',
  },
  about: {
    title: 'About CadArena - AI Architecture Studio',
    description: 'Learn about CadArena, our mission, and how we\'re revolutionizing architectural design.',
  },
};

/**
 * Update meta tags for a page
 */
export function updateMetaTags(meta) {
  const { title, description, keywords, ogImage, ogType, twitterCard, robots } = meta;

  // Title
  if (title) {
    document.title = title;
    updateMetaTag('og:title', title);
    updateMetaTag('twitter:title', title);
  }

  // Description
  if (description) {
    updateMetaTag('description', description);
    updateMetaTag('og:description', description);
    updateMetaTag('twitter:description', description);
  }

  // Keywords
  if (keywords) {
    updateMetaTag('keywords', keywords);
  }

  // Open Graph
  if (ogImage) {
    updateMetaTag('og:image', ogImage);
  }
  if (ogType) {
    updateMetaTag('og:type', ogType);
  }

  // Twitter Card
  if (twitterCard) {
    updateMetaTag('twitter:card', twitterCard);
  }

  // Robots
  if (robots) {
    updateMetaTag('robots', robots);
  }
}

/**
 * Helper to create or update meta tag
 */
function updateMetaTag(name, content) {
  const isProperty = name.startsWith('og:') || name.startsWith('twitter:');
  const selector = isProperty
    ? `meta[property="${name}"]`
    : `meta[name="${name}"]`;

  let element = document.querySelector(selector);

  if (!element) {
    element = document.createElement('meta');
    element[isProperty ? 'setAttribute' : 'name'] = name;
    document.head.appendChild(element);
  }

  element[isProperty ? 'setAttribute' : 'content'] = content;
}

/**
 * Structured data (JSON-LD) for rich snippets
 */
export function getStructuredData(type, data = {}) {
  const baseUrl = window.location.origin;
  const timestamp = new Date().toISOString();

  const schemas = {
    organization: {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'CadArena',
      url: baseUrl,
      logo: `${baseUrl}/logo.png`,
      description: 'AI-powered architectural CAD studio',
      sameAs: [
        'https://twitter.com/cadarena',
        'https://github.com/cadarena',
      ],
    },

    softwareApplication: {
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      name: 'CadArena Studio',
      description: 'AI-powered floor plan generation tool',
      url: `${baseUrl}/studio`,
      applicationCategory: 'DesignApplication',
      operatingSystem: 'Web',
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'USD',
      },
    },

    article: {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: data.title || 'CadArena Blog',
      description: data.description || '',
      image: data.image || `${baseUrl}/og-image.png`,
      datePublished: data.datePublished || timestamp,
      dateModified: data.dateModified || timestamp,
      author: {
        '@type': 'Organization',
        name: 'CadArena Team',
      },
    },

    breadcrumb: {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: (data.items || []).map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: item.name,
        item: `${baseUrl}${item.url}`,
      })),
    },
  };

  return schemas[type] || schemas.organization;
}

/**
 * Insert structured data into page
 */
export function insertStructuredData(schema) {
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(schema);
  document.head.appendChild(script);
}

/**
 * Accessibility announcements via aria-live regions
 */
export class AccessibilityAnnouncer {
  constructor() {
    // Create announcer regions if they don't exist
    ['polite', 'assertive'].forEach((level) => {
      if (!document.getElementById(`aria-announcer-${level}`)) {
        const region = document.createElement('div');
        region.id = `aria-announcer-${level}`;
        region.setAttribute('aria-live', level);
        region.setAttribute('aria-atomic', 'true');
        region.className = 'sr-only';
        document.body.appendChild(region);
      }
    });
  }

  /**
   * Announce a message to screen readers
   */
  announce(message, level = 'polite') {
    const region = document.getElementById(`aria-announcer-${level}`);
    if (region) {
      region.textContent = message;
      // Clear after announcement
      setTimeout(() => {
        region.textContent = '';
      }, 3000);
    }
  }

  /**
   * Announce loading state
   */
  announceLoading(operation = 'Operation') {
    this.announce(`${operation} in progress...`, 'polite');
  }

  /**
   * Announce completion
   */
  announceSuccess(message = 'Operation completed') {
    this.announce(message, 'polite');
  }

  /**
   * Announce error
   */
  announceError(error = 'An error occurred') {
    this.announce(`Error: ${error}`, 'assertive');
  }
}

/**
 * Keyboard navigation helper
 */
export class KeyboardNavigator {
  constructor(container) {
    this.container = container;
    this.focusableElements = [];
    this.currentFocusIndex = 0;
  }

  /**
   * Initialize keyboard navigation
   */
  init() {
    this.updateFocusableElements();
    this.container?.addEventListener('keydown', (e) => this.handleKeyDown(e));
  }

  /**
   * Update list of focusable elements
   */
  updateFocusableElements() {
    const selectors = [
      'button',
      'a[href]',
      'input',
      'textarea',
      'select',
      '[tabindex]',
    ];

    this.focusableElements = Array.from(
      this.container?.querySelectorAll(selectors.join(',')) || []
    ).filter((el) => !el.hasAttribute('disabled') && el.offsetParent);
  }

  /**
   * Handle keyboard events
   */
  handleKeyDown(event) {
    if (!this.focusableElements.length) return;

    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      event.preventDefault();
      this.focusNext();
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
      event.preventDefault();
      this.focusPrevious();
    } else if (event.key === 'Home') {
      event.preventDefault();
      this.focusFirst();
    } else if (event.key === 'End') {
      event.preventDefault();
      this.focusLast();
    }
  }

  /**
   * Focus next element
   */
  focusNext() {
    this.currentFocusIndex = (this.currentFocusIndex + 1) % this.focusableElements.length;
    this.focusCurrentElement();
  }

  /**
   * Focus previous element
   */
  focusPrevious() {
    this.currentFocusIndex = (this.currentFocusIndex - 1 + this.focusableElements.length) % this.focusableElements.length;
    this.focusCurrentElement();
  }

  /**
   * Focus first element
   */
  focusFirst() {
    this.currentFocusIndex = 0;
    this.focusCurrentElement();
  }

  /**
   * Focus last element
   */
  focusLast() {
    this.currentFocusIndex = this.focusableElements.length - 1;
    this.focusCurrentElement();
  }

  /**
   * Focus current element
   */
  focusCurrentElement() {
    this.focusableElements[this.currentFocusIndex]?.focus();
  }
}

/**
 * Skip to main content link for accessibility
 */
export function createSkipLink(mainContentSelector = 'main') {
  const skipLink = document.createElement('a');
  skipLink.href = `#${mainContentSelector}`;
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'skip-link';
  skipLink.style.cssText = `
    position: absolute;
    top: -40px;
    left: 0;
    background: #000;
    color: #fff;
    padding: 8px 16px;
    z-index: 100;
    text-decoration: none;
    border-radius: 0 0 4px 0;
  `;

  skipLink.addEventListener('focus', () => {
    skipLink.style.top = '0';
  });

  skipLink.addEventListener('blur', () => {
    skipLink.style.top = '-40px';
  });

  document.body.insertBefore(skipLink, document.body.firstChild);
}

/**
 * Check accessibility issues
 */
export function auditAccessibility() {
  const issues = [];

  // Check for images without alt text
  document.querySelectorAll('img').forEach((img) => {
    if (!img.alt && img.role !== 'presentation') {
      issues.push(`Image missing alt text: ${img.src}`);
    }
  });

  // Check for buttons without text
  document.querySelectorAll('button').forEach((btn) => {
    if (!btn.textContent?.trim() && !btn.getAttribute('aria-label')) {
      issues.push('Button without text or aria-label');
    }
  });

  // Check for form inputs without labels
  document.querySelectorAll('input').forEach((input) => {
    if (!input.id || !document.querySelector(`label[for="${input.id}"]`)) {
      if (!input.getAttribute('aria-label')) {
        issues.push(`Input without label: ${input.name}`);
      }
    }
  });

  // Check for color contrast (basic check)
  document.querySelectorAll('[style*="color"]').forEach((el) => {
    const style = window.getComputedStyle(el);
    const bgColor = style.backgroundColor;
    const fgColor = style.color;
    // Note: Real contrast checking requires color parsing library
    // This is just a placeholder for awareness
  });

  return issues;
}

export default {
  META_TAGS,
  updateMetaTags,
  getStructuredData,
  insertStructuredData,
  AccessibilityAnnouncer,
  KeyboardNavigator,
  createSkipLink,
  auditAccessibility,
};
