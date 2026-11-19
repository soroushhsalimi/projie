/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f6f7f9',
          100: '#eceef2',
          200: '#d5d9e2',
          300: '#b0b8c8',
          400: '#8591a8',
          500: '#66738c',
          600: '#505b73',
          700: '#414a5e',
          800: '#394050',
          900: '#131a2a',
          950: '#0b1220',
        },
        teal: {
          50: '#effbf9',
          100: '#d7f6f1',
          200: '#b0ece3',
          300: '#7bdcd0',
          400: '#43c4b7',
          500: '#1aa79c',
          600: '#0f877f',
          700: '#106c67',
          800: '#115654',
          900: '#124845',
          950: '#032b2a',
        },
        sand: {
          50: '#fbf9f4',
          100: '#f5f0e5',
          200: '#ebe1cc',
          300: '#ddcba7',
          400: '#ccae7d',
          500: '#bd955d',
          600: '#a97e4b',
          700: '#8c633f',
          800: '#735138',
          900: '#604432',
        },
        gold: {
          300: '#e8c98c',
          400: '#dcb466',
          500: '#d0a04a',
        },
      },
      fontFamily: {
        sans: ['Vazirmatn', 'Segoe UI', 'Tahoma', 'sans-serif'],
      },
      boxShadow: {
        card: '0 24px 60px -24px rgba(11, 18, 32, 0.25), 0 2px 8px rgba(11, 18, 32, 0.04)',
        glow: '0 18px 45px -18px rgba(26, 167, 156, 0.65)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 550ms cubic-bezier(0.22, 1, 0.36, 1) both',
        float: 'float 7s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
