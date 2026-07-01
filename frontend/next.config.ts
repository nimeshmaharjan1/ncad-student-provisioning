import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/quercus/:path*", destination: `${API_URL}/quercus/:path*` },
      { source: "/ldap/:path*", destination: `${API_URL}/ldap/:path*` },
      { source: "/google/:path*", destination: `${API_URL}/google/:path*` },
      { source: "/canvas/:path*", destination: `${API_URL}/canvas/:path*` },
      { source: "/library/:path*", destination: `${API_URL}/library/:path*` },
      { source: "/athens/:path*", destination: `${API_URL}/athens/:path*` },
    ];
  },
};

export default nextConfig;