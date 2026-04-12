/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        indigo: {
          450: '#5B52F0',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(79,70,229,0.25), transparent)',
      },
      animation: {
        'fade-in':    'fadeIn 0.5s ease-out both',
        'slide-up':   'slideUp 0.4s ease-out both',
        'scale-in':   'scaleIn 0.3s ease-out both',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'spin-slow':  'spin 8s linear infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' },                              to: { opacity: '1' } },
        slideUp: { from: { transform: 'translateY(16px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
        scaleIn: { from: { transform: 'scale(0.95)', opacity: '0' },    to: { transform: 'scale(1)',    opacity: '1' } },
      },
      boxShadow: {
        'glow-indigo': '0 0 40px -8px rgba(79,70,229,0.5)',
        'glow-sm':     '0 0 20px -4px rgba(79,70,229,0.3)',
        'card':        '0 4px 24px -4px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
};
