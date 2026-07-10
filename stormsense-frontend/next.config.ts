import type { NextConfig } from "next";

// Falls back to 127.0.0.1 (not "localhost" — Node can resolve "localhost" to
// IPv6 first, which fails/resets since uvicorn only binds IPv4) for local
// dev. Set NEXT_PUBLIC_API_URL in .env.local / your deployment platform
// to point at a deployed backend instead.
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // react-leaflet's Leaflet instance doesn't tear down fast enough across
  // React Strict Mode's intentional dev-only double-mount, which crashes
  // the map with "Map container is being reused by another instance".
  // This is a dev-only diagnostic mode — disabling it does not change
  // production behavior.
  reactStrictMode: false,
  async rewrites() {
    return [
      { source: "/api/backend/:path*", destination: `${BACKEND_URL}/:path*` },
    ];
  },
};

export default nextConfig;