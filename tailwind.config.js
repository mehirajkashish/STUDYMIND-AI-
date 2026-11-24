/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0D0D0D',
        sidebar: '#141414',
        card: '#1A1A1A',
        elevated: '#242424',
        obsidian: {
          canvas: '#0D0D0D',
          sidebar: '#141414',
          card: '#1A1A1A',
          hover: '#242424',
          border: '#262626',
          borderSubtle: '#222222',
          borderHover: '#3A3A3A',
          ghost: '#1F1F1F',
          ghostBorder: '#2E2E2E'
        },
        primary: {
          DEFAULT: '#FFFFFF',
          hover: '#E5E5E5',
          muted: 'rgba(255, 255, 255, 0.1)',
        },
        accent: {
          DEFAULT: '#4F8CFF',
          secondary: '#8B7CFF',
          cyan: '#35C6E8',
          emerald: '#22C55E'
        },
        border: {
          DEFAULT: '#262626',
          subtle: '#222222',
          strong: '#2E2E2E',
        },
        surface: {
          bg: '#0D0D0D',
          sidebar: '#141414',
          card: '#1A1A1A',
          elevated: '#242424',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#9A9A9A',
          muted: '#666666',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['"Instrument Serif"', '"Playfair Display"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'framer-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.5), 0 0 0 1px #262626',
        'framer-card': '0 4px 20px -2px rgba(0, 0, 0, 0.6), 0 0 0 1px #262626',
        'framer-elevated': '0 10px 30px -4px rgba(0, 0, 0, 0.7), 0 0 0 1px #2E2E2E',
      }
    },
  },
  plugins: [],
}
