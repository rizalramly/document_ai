/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: { DEFAULT: '#3b82f6', dark: '#2563eb' },
                surface: { dark: '#1a1f2e', DEFAULT: '#111827' },
                'bg-dark': '#0f1219',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
