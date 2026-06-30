import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  rewrites: async () => [
    {
      source: "/quercus/:path*",
      destination: "http://127.0.0.1:8000/quercus/:path*",
    },
    {
      source: "/ldap/:path*",
      destination: "http://127.0.0.1:8000/ldap/:path*",
    },
    {
      source: "/google/:path*",
      destination: "http://127.0.0.1:8000/google/:path*",
    },
    {
      source: "/export/:path*",
      destination: "http://127.0.0.1:8000/export/:path*",
    },
  ],
}

export default nextConfig
