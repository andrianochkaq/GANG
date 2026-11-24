import type { Config } from 'tailwindcss';

// Tailwind is mapped to the design-system CSS variables (tokens.json), so
// utilities never carry raw colours or sizes. Components use the fc-*
// classes from docs/design-system/components.css.
const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      bg: 'var(--bg)',
      soft: 'var(--soft)',
      line: 'var(--line)',
      accent: 'var(--accent)',
      ink: 'var(--ink)',
      surface: 'var(--surface)',
      text: 'var(--text)',
      'text-secondary': 'var(--text-secondary)',
      'text-muted': 'var(--text-muted)',
      'text-subtle': 'var(--text-subtle)',
      danger: 'var(--danger)',
    },
    fontFamily: {
      display: 'var(--font-display)',
      text: 'var(--font-text)',
    },
    borderRadius: {
      sm: 'var(--radius-sm)',
      md: 'var(--radius-md)',
      lg: 'var(--radius-lg)',
      card: 'var(--radius-card)',
      pill: 'var(--radius-pill)',
    },
    extend: {},
  },
  plugins: [],
};

export default config;
