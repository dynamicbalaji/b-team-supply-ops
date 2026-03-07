/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        'syne': ['Syne', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'slide': 'slide 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        slide: {
          '0%': { transform: 'translateX(-100%) skewX(-12deg)' },
          '50%': { transform: 'translateX(100vw) skewX(-12deg)' },
          '100%': { transform: 'translateX(-100%) skewX(-12deg)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 5px currentColor' },
          '50%': { boxShadow: '0 0 20px currentColor, 0 0 30px currentColor' },
        },
        'pulse-glow': {
          '0%, 100%': { 
            boxShadow: '0 0 5px rgba(0, 212, 255, 0.3)',
            transform: 'scale(1)',
          },
          '50%': { 
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.6), 0 0 30px rgba(0, 212, 255, 0.4)',
            transform: 'scale(1.05)',
          },
        },
      },
    },
  },
  plugins: [],
}
