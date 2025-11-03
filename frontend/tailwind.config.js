/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Blackalgo-inspired color palette
        'blackalgo': {
          'bg-dark': '#0B0D17',
          'bg-darker': '#000008',
          'purple-light': '#9B8FFF',
          'purple': '#6d4cff',
          'purple-dark': '#5a3ce6',
          'cyan': '#00FFD1',
          'cyan-dark': '#00D9FF',
          'text-light': '#edecf9',
          'text-muted': '#a8a7b8',
          'accent': '#9B8FFF',
        },
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
    },
  },
  plugins: [],
}
