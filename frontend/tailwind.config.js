/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      colors: {
        cyber: {
          950: '#030712', // Pure deep dark background
          900: '#0b0f19',
          800: '#111827',
          700: '#1f2937',
          primary: '#4f46e5', // Indigo Glow
          secondary: '#06b6d4', // Stockholm Royal Blue/Cyan
          accent: '#f59e0b', // Stockholm Gold
          emerald: '#10b981', // Compliant Green
          rose: '#f43f5e', // Risk Alert Red
        }
      }
    },
  },
  plugins: [],
}
