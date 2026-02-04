/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'stock-up': '#ef4444',    // 红色涨
        'stock-down': '#22c55e',  // 绿色跌 (A股习惯)
      },
    },
  },
  plugins: [],
};
