import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // react-leaflet's Leaflet instance doesn't tear down fast enough across
  // React Strict Mode's intentional dev-only double-mount, which crashes
  // the map with "Map container is being reused by another instance".
  // This is a dev-only diagnostic mode — disabling it does not change
  // production behavior.
  reactStrictMode: false,
  async rewrites() {
    // Use 127.0.0.1 explicitly, not "localhost" — Node can resolve "localhost"
    // to IPv6 (::1) first, which fails/resets since uvicorn only binds IPv4,
    // causing intermittent "socket hang up" errors on this proxy route.
    return [
      { source: "/api/backend/:path*", destination: "http://127.0.0.1:8000/:path*" },
    ];
  },
};

export default nextConfig;