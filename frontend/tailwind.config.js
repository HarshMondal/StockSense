import animate from 'tailwindcss-animate';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#0b0f1a',
          soft: '#111827',
          card: '#0f1626',
        },
        line: '#1f2937',
        accent: {
          DEFAULT: '#38bdf8',
          soft: '#0ea5e9',
        },
        good: '#22c55e',
        bad: '#ef4444',
        warn: '#f59e0b',
        muted: '#94a3b8',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [animate],
};
