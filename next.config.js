/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // ESLint チェックをスキップする
    ignoreDuringBuilds: true,
  },
  typescript: {
    // TypeScript チェックをスキップする
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
