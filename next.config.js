/** @type {import('next').NextConfig} */
const nextConfig = {
  // Render 全栈部署，使用服务端渲染
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
