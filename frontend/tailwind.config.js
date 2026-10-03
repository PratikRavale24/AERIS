/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--color-bg-canvas)',
        panel: 'var(--color-bg-panel)',
        raised: 'var(--color-bg-raised)',
        'surface-hover': 'var(--color-bg-hover)',
        inset: 'var(--color-bg-inset)',
        
        'border-subtle': 'var(--color-border-subtle)',
        'border-default': 'var(--color-border)',
        'border-strong': 'var(--color-border-strong)',
        
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',
        
        'header-bg': 'var(--color-header-bg)',
        
        primary: 'var(--color-primary)',
        'primary-strong': 'var(--color-primary-strong)',
        
        ok: 'var(--color-ok)',
        'ok-text': 'var(--color-ok-text)',
        advisory: 'var(--color-advisory)',
        'advisory-text': 'var(--color-advisory-text)',
        caution: 'var(--color-caution)',
        'caution-text': 'var(--color-caution-text)',
        high: 'var(--color-high)',
        'high-text': 'var(--color-high-text)',
        critical: 'var(--color-critical)',
        'critical-text': 'var(--color-critical-text)',
        simulation: 'var(--color-simulation)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'panel': '6px',
      },
      fontSize: {
        'metric': ['28px', { lineHeight: '1.1', fontWeight: '700' }],
        'section': ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        'card-title': ['14px', { lineHeight: '1.4', fontWeight: '600' }],
      },
    },
  },
  plugins: [],
}
