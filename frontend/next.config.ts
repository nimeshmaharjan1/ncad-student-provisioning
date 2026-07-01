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
      source: "/canvas/:path*",
      destination: "http://127.0.0.1:8000/canvas/:path*",
    },
    {
      source: "/library/:path*",
      destination: "http://127.0.0.1:8000/library/:path*",
    },
    {
      source: "/athens/:path*",
      destination: "http://127.0.0.1:8000/athens/:path*",
    },
  ],
}

export default nextConfig
