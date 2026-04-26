/**
 * Performance monitoring and optimization utilities
 * Tracks metrics, identifies bottlenecks
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.marks = new Map();
    this.thresholds = {
      pageLoad: 3000,    // 3 seconds
      apiCall: 5000,     // 5 seconds
      interaction: 100,  // 100ms (INP)
      paint: 2500,       // 2.5 seconds (LCP)
    };
  }

  /**
   * Start timing a task
   */
  start(label) {
    this.marks.set(label, performance.now());
  }

  /**
   * End timing and record metric
   */
  end(label, category = 'custom') {
    const startTime = this.marks.get(label);
    if (!startTime) {
      console.warn(`No start mark for ${label}`);
      return null;
    }

    const duration = performance.now() - startTime;
    const metric = {
      label,
      category,
      duration,
      timestamp: new Date().toISOString(),
      slow: duration > this.thresholds[category],
    };

    if (!this.metrics.has(category)) {
      this.metrics.set(category, []);
    }
    this.metrics.get(category).push(metric);

    if (metric.slow) {
      console.warn(`⚠️ Slow ${category}: ${label} took ${duration.toFixed(2)}ms`);
    }

    this.marks.delete(label);
    return metric;
  }

  /**
   * Measure specific operation
   */
  async measure(label, asyncFn, category = 'custom') {
    this.start(label);
    try {
      const result = await asyncFn();
      this.end(label, category);
      return result;
    } catch (error) {
      this.end(label, category);
      throw error;
    }
  }

  /**
   * Get metrics for a category
   */
  getMetrics(category) {
    return this.metrics.get(category) || [];
  }

  /**
   * Get average duration for a category
   */
  getAverageDuration(category) {
    const metrics = this.getMetrics(category);
    if (metrics.length === 0) return 0;
    const total = metrics.reduce((sum, m) => sum + m.duration, 0);
    return total / metrics.length;
  }

  /**
   * Report all metrics
   */
  report() {
    const report = {};
    for (const [category, metrics] of this.metrics.entries()) {
      const slowCount = metrics.filter((m) => m.slow).length;
      const avgDuration = this.getAverageDuration(category);
      report[category] = {
        count: metrics.length,
        avgDuration: avgDuration.toFixed(2),
        slowCount,
        metrics,
      };
    }
    return report;
  }

  /**
   * Clear metrics
   */
  clear() {
    this.metrics.clear();
    this.marks.clear();
  }

  /**
   * Send metrics to analytics
   */
  sendToAnalytics() {
    const report = this.report();
    if (process.env.REACT_APP_ENABLE_ANALYTICS) {
      // Send to your analytics provider
      console.log('📊 Analytics:', report);
      // Example: sendToDatadog(report);
    }
  }
}

/**
 * Web Vitals tracking
 */
export class WebVitalsTracker {
  constructor() {
    this.vitals = {};
  }

  /**
   * Track Largest Contentful Paint (LCP)
   */
  trackLCP() {
    if (!('PerformanceObserver' in window)) return;

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.vitals.lcp = {
          value: lastEntry.renderTime || lastEntry.loadTime,
          timestamp: new Date().toISOString(),
        };
      });

      observer.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (error) {
      console.warn('LCP tracking failed:', error);
    }
  }

  /**
   * Track Cumulative Layout Shift (CLS)
   */
  trackCLS() {
    if (!('PerformanceObserver' in window)) return;

    try {
      let clsValue = 0;
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        this.vitals.cls = {
          value: clsValue,
          timestamp: new Date().toISOString(),
        };
      });

      observer.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      console.warn('CLS tracking failed:', error);
    }
  }

  /**
   * Track First Input Delay (FID) / Interaction to Next Paint (INP)
   */
  trackInteractivity() {
    if (!('PerformanceObserver' in window)) return;

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          this.vitals.inp = {
            value: entry.processingDuration,
            timestamp: new Date().toISOString(),
          };
        });
      });

      observer.observe({ entryTypes: ['first-input', 'event'] });
    } catch (error) {
      console.warn('Interactivity tracking failed:', error);
    }
  }

  /**
   * Get all tracked vitals
   */
  getVitals() {
    return this.vitals;
  }

  /**
   * Check if vitals are within acceptable ranges
   */
  areVitalsHealthy() {
    const thresholds = {
      lcp: 2500,  // LCP should be under 2.5s
      cls: 0.1,   // CLS should be under 0.1
      inp: 200,   // INP should be under 200ms
    };

    const healthy = {};
    for (const [metric, value] of Object.entries(this.vitals)) {
      healthy[metric] = value.value < thresholds[metric];
    }
    return healthy;
  }
}

/**
 * Memory usage monitoring
 */
export function monitorMemory() {
  if (!performance.memory) {
    console.warn('Memory API not available in this browser');
    return null;
  }

  const { jsHeapSizeLimit, totalJSHeapSize, usedJSHeapSize } = performance.memory;
  const usagePercentage = (usedJSHeapSize / jsHeapSizeLimit) * 100;

  return {
    usedJSHeapSize: (usedJSHeapSize / 1048576).toFixed(2), // MB
    totalJSHeapSize: (totalJSHeapSize / 1048576).toFixed(2),
    jsHeapSizeLimit: (jsHeapSizeLimit / 1048576).toFixed(2),
    usagePercentage: usagePercentage.toFixed(2),
    healthy: usagePercentage < 80,
  };
}

/**
 * Bundle size analyzer
 */
export function analyzeBundleSize() {
  return {
    warning:
      'Use webpack-bundle-analyzer plugin to analyze bundle size',
    command: 'npm run build -- --analyze',
    docs: 'https://create-react-app.dev/docs/analyzing-the-bundle-size/',
  };
}

/**
 * Debug performance issues
 */
export function debugPerformance() {
  console.group('🔍 Performance Debug');

  // Navigation Timing
  console.group('Navigation Timing');
  if (window.performance && window.performance.timing) {
    const timing = performance.timing;
    const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
    const redirectTime = timing.redirectEnd - timing.redirectStart;
    const dnsTime = timing.domainLookupEnd - timing.domainLookupStart;
    const tcpTime = timing.connectEnd - timing.connectStart;
    const requestTime = timing.responseStart - timing.requestStart;
    const responseTime = timing.responseEnd - timing.responseStart;
    const domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
    const interactiveTime = timing.domInteractive - timing.navigationStart;

    console.table({
      pageLoadTime,
      redirectTime,
      dnsTime,
      tcpTime,
      requestTime,
      responseTime,
      domReadyTime,
      interactiveTime,
    });
  }
  console.groupEnd();

  // Resource Timing
  console.group('Resource Timing');
  const resources = performance.getEntriesByType('resource');
  const resourceSummary = {
    totalResources: resources.length,
    totalSize: (resources.reduce((sum, r) => sum + (r.transferSize || 0), 0) / 1024).toFixed(2),
    slowestResource: resources.reduce((max, r) =>
      r.duration > max.duration ? r : max
    ),
    totalDuration: resources.reduce((sum, r) => sum + r.duration, 0).toFixed(2),
  };
  console.table(resourceSummary);
  console.groupEnd();

  // Memory
  console.group('Memory Usage');
  console.table(monitorMemory());
  console.groupEnd();

  console.groupEnd();
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();
const webVitalsTracker = new WebVitalsTracker();

export { performanceMonitor, webVitalsTracker };

export default {
  PerformanceMonitor,
  WebVitalsTracker,
  monitorMemory,
  analyzeBundleSize,
  debugPerformance,
  performanceMonitor,
  webVitalsTracker,
};
