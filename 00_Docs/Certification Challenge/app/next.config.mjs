/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: import.meta.dirname,
  outputFileTracingIncludes: {
    "/api/chat": ["./data/**/*"],
  },
};

export default nextConfig;
