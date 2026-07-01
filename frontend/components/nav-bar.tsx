"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"

const links = [
  { href: "/", label: "Home" },
  { href: "/quercus", label: "Quercus" },
  { href: "/library", label: "Library" },
  { href: "/guide", label: "Guide" },
]

export function NavBar() {
  const pathname = usePathname()

  return (
    <nav className="border-b">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <Link
          href="/"
          className="text-sm font-semibold tracking-tight hover:text-primary"
        >
          NCAD
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {links.map((link) => {
            const isActive = link.href === "/"
              ? pathname === "/"
              : pathname === link.href || pathname.startsWith(link.href + "/")
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "transition-colors",
                  isActive
                    ? "font-medium text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
