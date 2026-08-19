import type { NextConfig } from "next";

const API_URL = "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/quercus/:path*", destination: `${API_URL}/quercus/:path*` },
      { source: "/ldap/:path*", destination: `${API_URL}/ldap/:path*` },
      { source: "/google/:path*", destination: `${API_URL}/google/:path*` },
      { source: "/canvas/:path*", destination: `${API_URL}/canvas/:path*` },
      { source: "/staff/canvas/:path*", destination: `${API_URL}/staff/canvas/:path*` },
      { source: "/staff/library/:path*", destination: `${API_URL}/staff/library/:path*` },
      { source: "/library/:path*", destination: `${API_URL}/library/:path*` },
      { source: "/athens/:path*", destination: `${API_URL}/athens/:path*` },
      { source: "/admin/:path*", destination: `${API_URL}/admin/:path*` },
    ];
  },
};

export default nextConfig;