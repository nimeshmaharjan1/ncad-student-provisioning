/*
 * Root layout — wraps the entire app in PipelineProvider so Quercus state
 * (cleaned CSV file) persists across page navigation.
 *
 * Navigation is split into two logical routes:
 *   /quercus  — main provisioning pipeline (Quercus → LDAP → Canvas → Google)
 *   /library  — standalone Library export (no dependency on Quercus state)
 *
 * Rationale for separate pages:
 *   Library accepts its own raw Quercus export files and transforms them into
 *   the Library upload schema. It does NOT use PipelineContext. Putting it on
 *   its own page avoids confusion that it is a "step 5" of the pipeline.
 *
 * The top nav bar uses Next.js <Link> for client-side transitions, preserving
 * PipelineContext state across route changes.
 */

import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"

export const metadata: Metadata = {
  title: "NCAD Student Provisioning",
}

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { PipelineProvider } from "@/lib/pipeline-context"
import { NavBar } from "@/components/nav-bar"
import { cn } from "@/lib/utils"

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" })

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("antialiased", fontMono.variable, "font-sans", geist.variable)}
    >
      <body>
        <ThemeProvider>
          <PipelineProvider>
            <nav className="border-b">
              <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
                <Link
                  href="/"
                  className="text-sm font-semibold tracking-tight hover:text-primary"
                >
                  NCAD
                </Link>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <Link href="/" className="hover:text-foreground transition-colors">
                    Home
                  </Link>
                  <Link href="/quercus" className="hover:text-foreground transition-colors">
                    Quercus
                  </Link>
                  <Link href="/library" className="hover:text-foreground transition-colors">
                    Library
                  </Link>
                </div>
              </div>
            </nav>
            {children}
          </PipelineProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
