import type { NextConfig } from "next";

const apiHost =
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiHost.replace(/\/+$/, "")}/api/:path*`,
      },
      {
        source: "/v1/:path*",
        destination: `${apiHost.replace(/\/+$/, "")}/v1/:path*`,
      },
      {
        source: "/health",
        destination: `${apiHost.replace(/\/+$/, "")}/health`,
      },
    ];
  },
};

export default nextConfig;
