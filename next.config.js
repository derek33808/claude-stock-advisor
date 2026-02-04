/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // 静态导出，用于 Netlify
  images: {
    unoptimized: true,  // 静态导出需要
  },
};

module.exports = nextConfig;
