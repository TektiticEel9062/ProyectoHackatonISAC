/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#0B0F19',
        surface: '#111827',
        borderTac: '#1F2937',
        offensive: '#00F5D4',
        defensive: '#F59E0B',
        risk: '#F43F5E',
        advanced360: '#8B5CF6',
        pitchLine: '#334155',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
