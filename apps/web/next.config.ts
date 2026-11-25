import type { NextConfig } from "next";

const combined = process.env.RAILWAY_COMBINED_BUILD === "1";
const apiInternal = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (!combined) {
      return [];
    }
    return [
      { source: "/api/v1/:path*", destination: `${apiInternal}/api/v1/:path*` },
      { source: "/health", destination: `${apiInternal}/health` },
      { source: "/ready", destination: `${apiInternal}/ready` },
    ];
  },
};

export default nextConfig;
