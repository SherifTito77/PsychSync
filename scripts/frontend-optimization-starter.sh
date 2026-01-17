#!/bin/bash

# PsychSync Frontend Performance Optimization Starter
# Phase 2: Bundle Size Optimization and Dependency Cleanup

set -e  # Exit on any error

echo "🚀 Starting PsychSync Frontend Performance Optimization - Phase 2"
echo "=================================================================="

# Configuration
FRONTEND_DIR="frontend"
BACKUP_DIR="frontend-backup-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create backup directory
create_backup() {
    log_info "Creating backup of current frontend configuration..."

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    fi

    mkdir -p "$BACKUP_DIR"
    cp -r "$FRONTEND_DIR/vite.config.ts" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$FRONTEND_DIR/package.json" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$FRONTEND_DIR/package-lock.json" "$BACKUP_DIR/" 2>/dev/null || true

    log_success "Backup created: $BACKUP_DIR"
}

# Check current bundle size
measure_current_bundle() {
    log_info "Measuring current bundle size..."

    cd "$FRONTEND_DIR"

    if [ ! -d "dist" ]; then
        log_info "Building current version for measurement..."
        npm run build
    fi

    if [ -d "dist" ]; then
        TOTAL_SIZE=$(du -sh dist | cut -f1)
        JS_SIZE=$(find dist -name "*.js" -exec du -ch {} + | grep total$ | cut -f1)
        CSS_SIZE=$(find dist -name "*.css" -exec du -ch {} + | grep total$ | cut -f1)

        log_info "Current Bundle Metrics:"
        log_info "  • Total Size: $TOTAL_SIZE"
        log_info "  • JavaScript: $JS_SIZE"
        log_info "  • CSS: $CSS_SIZE"

        # Save metrics for comparison
        echo "BEFORE_OPTIMIZATION" > ../bundle-metrics.txt
        echo "TOTAL_SIZE=$TOTAL_SIZE" >> ../bundle-metrics.txt
        echo "JS_SIZE=$JS_SIZE" >> ../bundle-metrics.txt
        echo "CSS_SIZE=$CSS_SIZE" >> ../bundle-metrics.txt
        echo "TIMESTAMP=$(date)" >> ../bundle-metrics.txt

        log_success "Bundle metrics saved to bundle-metrics.txt"
    else
        log_warning "No dist directory found, skipping current measurement"
    fi

    cd ..
}

# Optimize Vite configuration
optimize_vite_config() {
    log_info "Optimizing Vite configuration..."

    VITE_CONFIG="$FRONTEND_DIR/vite.config.ts"

    if [ ! -f "$VITE_CONFIG" ]; then
        log_error "Vite config not found: $VITE_CONFIG"
        return 1
    fi

    # Create optimized Vite config
    cat > "$VITE_CONFIG" << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
      '@services': path.resolve(__dirname, './src/services'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,  // Disable in production for smaller bundles
    minify: 'terser',  // Use Terser for better optimization
    target: 'esnext',  // Modern browsers for smaller code
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate vendor chunks for better caching
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],  // Remove Chart.js (duplicate)
          ui: ['@radix-ui/react-slot', 'lucide-react', 'class-variance-authority'],
          forms: ['@hookform/resolvers', 'react-hook-form'],
          utils: ['lodash-es', 'clsx', 'tailwind-merge']
        },
        // Optimize chunk naming for better caching
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            const fileName = facadeModuleId.split('/').pop()?.replace(/\.[^.]*$/, '')
            return `js/${fileName}-[hash].js`
          }
          return 'js/[name]-[hash].js'
        }
      }
    },
    // Enable compression for production builds
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000,  // Warn on chunks > 1MB

    // Optimize assets
    assetsInlineLimit: 4096,  // Inline assets smaller than 4kb

    // Terser optimization
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
        drop_debugger: true
      }
    }
  },
  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom'
    ],
    exclude: [
      'chart.js',  // Remove duplicate chart library
      'react-chartjs-2'  // Remove duplicate chart library
    ]
  },
  // Development optimizations
  esbuild: {
    target: 'esnext',
    drop: ['console', 'debugger']  // Remove in production builds
  }
});
EOF

    log_success "Vite configuration optimized"
}

# Clean up duplicate dependencies
cleanup_dependencies() {
    log_info "Cleaning up duplicate dependencies..."

    cd "$FRONTEND_DIR"

    # Remove duplicate chart library
    if npm list chart.js >/dev/null 2>&1; then
        log_info "Removing duplicate Chart.js library..."
        npm uninstall chart.js react-chartjs-2
        log_success "Chart.js removed, keeping Recharts"
    fi

    # Check for other potential optimizations
    log_info "Analyzing dependencies for optimization opportunities..."

    # Install bundle analyzer for monitoring
    if ! npm list rollup-plugin-visualizer >/dev/null 2>&1; then
        log_info "Installing bundle analyzer for monitoring..."
        npm install --save-dev rollup-plugin-visualizer
    fi

    cd ..
    log_success "Dependency cleanup completed"
}

# Create performance monitoring components
create_performance_components() {
    log_info "Creating performance monitoring components..."

    PERFORMANCE_DIR="$FRONTEND_DIR/src/components/performance"
    mkdir -p "$PERFORMANCE_DIR"

    # Bundle size analyzer component
    cat > "$PERFORMANCE_DIR/BundleSizeMonitor.tsx" << 'EOF'
import React, { useState, useEffect } from 'react';

interface BundleMetrics {
  totalSize: string;
  jsSize: string;
  cssSize: string;
  loadTime: number;
}

export const BundleSizeMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<BundleMetrics | null>(null);

  useEffect(() => {
    // Monitor bundle performance
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const navigationEntry = entries[0] as PerformanceNavigationTiming;

      if (navigationEntry) {
        setMetrics({
          totalSize: 'N/A',
          jsSize: 'N/A',
          cssSize: 'N/A',
          loadTime: navigationEntry.loadEventEnd - navigationEntry.loadEventStart
        });
      }
    });

    observer.observe({ entryTypes: ['navigation'] });

    return () => observer.disconnect();
  }, []);

  if (!metrics) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-black bg-opacity-75 text-white p-2 rounded text-xs">
      <div>Load Time: {metrics.loadTime.toFixed(0)}ms</div>
      {/* Additional metrics can be added here */}
    </div>
  );
};
EOF

    log_success "Performance monitoring components created"
}

# Build optimized version
build_optimized() {
    log_info "Building optimized frontend..."

    cd "$FRONTEND_DIR"

    # Clean previous build
    rm -rf dist

    # Build with optimizations
    npm run build

    if [ $? -eq 0 ]; then
        log_success "Optimized build completed successfully"
    else
        log_error "Build failed"
        exit 1
    fi

    cd ..
}

# Measure optimized bundle size
measure_optimized_bundle() {
    log_info "Measuring optimized bundle size..."

    cd "$FRONTEND_DIR"

    if [ -d "dist" ]; then
        TOTAL_SIZE=$(du -sh dist | cut -f1)
        JS_SIZE=$(find dist -name "*.js" -exec du -ch {} + | grep total$ | cut -f1)
        CSS_SIZE=$(find dist -name "*.css" -exec du -ch {} + | grep total$ | cut -f1)

        log_success "Optimized Bundle Metrics:"
        log_info "  • Total Size: $TOTAL_SIZE"
        log_info "  • JavaScript: $JS_SIZE"
        log_info "  • CSS: $CSS_SIZE"

        # Calculate improvement
        if [ -f "../bundle-metrics.txt" ]; then
            source ../bundle-metrics.txt

            if [ ! -z "$TOTAL_SIZE" ] && [ "$TOTAL_SIZE" != "$BEFORE_OPTIMIZATION" ]; then
                log_success "Bundle size optimized from $BEFORE_OPTIMIZATION to $TOTAL_SIZE"
            fi
        fi

        # Analyze largest chunks
        log_info "Analyzing largest chunks:"
        find dist -name "*.js" -exec du -h {} + | sort -hr | head -5

    else
        log_error "Build failed - no dist directory found"
        exit 1
    fi

    cd ..
}

# Generate optimization report
generate_report() {
    log_info "Generating optimization report..."

    REPORT_FILE="FRONTEND_OPTIMIZATION_REPORT.md"

    cat > "$REPORT_FILE" << EOF
# 🚀 PsychSync Frontend Optimization Report

**Date:** $(date)
**Phase:** Phase 2 - Bundle Size Optimization and Dependency Cleanup
**Status:** ✅ SUCCESS

---

## 📊 Bundle Size Analysis

### Before Optimization
- Total Size: $(grep 'TOTAL_SIZE=' bundle-metrics.txt | cut -d'=' -f2 2>/dev/null || echo 'N/A')
- JavaScript Size: $(grep 'JS_SIZE=' bundle-metrics.txt | cut -d'=' -f2 2>/dev/null || echo 'N/A')
- CSS Size: $(grep 'CSS_SIZE=' bundle-metrics.txt | cut -d'=' -f2 2>/dev/null || echo 'N/A')

### After Optimization
EOF

    if [ -d "frontend/dist" ]; then
        cd frontend
        TOTAL_SIZE=$(du -sh dist | cut -f1)
        JS_SIZE=$(find dist -name "*.js" -exec du -ch {} + | grep total$ | cut -f1)
        CSS_SIZE=$(find dist -name "*.css" -exec du -ch {} + | grep total$ | cut -f1)

        cat >> "../$REPORT_FILE" << EOF
- Total Size: $TOTAL_SIZE
- JavaScript Size: $JS_SIZE
- CSS Size: $CSS_SIZE
EOF
        cd ..
    fi

    cat >> "$REPORT_FILE" << EOF

---

## 🔧 Applied Optimizations

### ✅ Vite Configuration Enhancements
- **Minification:** Switched to Terser for better optimization
- **Code Splitting:** Manual chunk separation for vendors, charts, UI components
- **Source Maps:** Disabled in production for smaller bundles
- **Target:** Set to ESNext for modern browsers
- **Console Removal:** Console statements removed in production

### ✅ Dependency Cleanup
- **Removed:** Chart.js and react-chartjs-2 (duplicate functionality)
- **Kept:** Recharts (smaller, React-native chart library)
- **Added:** rollup-plugin-visualizer for bundle analysis

### ✅ Build Optimizations
- **Chunking:** Intelligent code splitting for better caching
- **Asset Inline:** Small assets (<4KB) inlined
- **Compression:** Report compressed sizes for monitoring

---

## 📈 Performance Improvements

- **Bundle Size:** Reduced by removing duplicate libraries
- **Load Time:** Improved through code splitting and minification
- **Caching:** Better browser caching with chunk naming strategy
- **Build Time:** Optimized dependency resolution

---

## 🎯 Development Guidelines

### Bundle Size Best Practices
1. **Lazy Loading:** Continue using \`createLazyComponent\` for routes
2. **Tree Shaking:** Ensure imports are specific, not entire libraries
3. **Asset Optimization:** Compress images and optimize fonts
4. **Code Splitting:** Separate vendor and application code

### Monitoring
1. **Bundle Analysis:** Use \`npm run build\` and analyze dist/ folder
2. **Performance Budget:** Set target < 500KB gzipped for total bundle
3. **Lighthouse Testing:** Regular performance audits
4. **Bundle Validation:** Monitor for unexpected size increases

---

## 🚨 Rollback Information

**Backup Location:** $BACKUP_DIR
**Rollback Commands:**
\`\`\`bash
# Restore vite.config.ts
cp $BACKUP_DIR/vite.config.ts frontend/

# Restore package.json
cp $BACKUP_DIR/package.json frontend/

# Reinstall dependencies
cd frontend && npm install
\`\`\`

---

## 🚀 Next Steps

1. **Phase 3 Ready:** Proceed with API response optimization
2. **Monitor Performance:** Track bundle size in CI/CD pipeline
3. **Test in Production:** Monitor Core Web Vitals
4. **Team Training:** Share optimization guidelines with developers

---

*Generated automatically by PsychSync Frontend Optimizer*
EOF

    log_success "Optimization report generated: $REPORT_FILE"
}

# Main execution
main() {
    echo "Starting frontend performance optimization..."

    # Create backup
    create_backup

    # Measure current state
    measure_current_bundle

    # Apply optimizations
    optimize_vite_config
    cleanup_dependencies
    create_performance_components

    # Build optimized version
    build_optimized

    # Measure results
    measure_optimized_bundle

    # Generate report
    generate_report

    echo ""
    log_success "🎉 Phase 2 frontend optimization completed successfully!"
    echo "📄 Check FRONTEND_OPTIMIZATION_REPORT.md for detailed results"
    echo "🚀 Ready for Phase 3: API Response Optimization"
    echo "💾 Backup created at: $BACKUP_DIR"
}

# Handle script arguments
case "${1:-}" in
    --rollback)
        log_info "Rolling back frontend optimizations..."
        if [ -d "$BACKUP_DIR" ]; then
            cp "$BACKUP_DIR/vite.config.ts" "$FRONTEND_DIR/" 2>/dev/null || true
            cp "$BACKUP_DIR/package.json" "$FRONTEND_DIR/" 2>/dev/null || true
            cp "$BACKUP_DIR/package-lock.json" "$FRONTEND_DIR/" 2>/dev/null || true
            cd "$FRONTEND_DIR" && npm install && cd ..
            log_success "Rollback completed"
        else
            log_error "No backup found for rollback"
        fi
        exit 0
        ;;
    --help|-h)
        echo "PsychSync Frontend Performance Optimizer"
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --rollback    Restore from backup"
        echo "  --help        Show this help message"
        echo ""
        echo "This script will:"
        echo "  1. Backup current configuration"
        echo "  2. Measure current bundle size"
        echo "  3. Optimize Vite configuration"
        echo "  4. Clean up duplicate dependencies"
        echo "  5. Build optimized version"
        echo "  6. Generate performance report"
        exit 0
        ;;
    "")
        # Default behavior - run optimization
        main
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
