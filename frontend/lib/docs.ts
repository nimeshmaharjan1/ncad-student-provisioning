export interface DocMeta {
  slug: string
  file: string
  title: string
  description: string
}

export const DOCS: DocMeta[] = [
  {
    slug: "user-guide",
    file: "USER_GUIDE.md",
    title: "User Guide",
    description:
      "How the system works end to end, from uploading Quercus exports to producing ready-to-upload files for LDAP, Canvas, Google Workspace, Athens and the Library.",
  },
  {
    slug: "automation-roadmap",
    file: "AUTOMATION_ROADMAP.md",
    title: "Automation Roadmap",
    description:
      "The plain-English plan for moving from the current manual process to zero-touch provisioning: glossary, decisions, risks, and what happens next.",
  },
  {
    slug: "manual-testing",
    file: "MANUAL_TESTING.md",
    title: "Manual Testing Guide",
    description:
      "Step-by-step test suites for every feature, including what to change in the sample files to trigger each scenario.",
  },
  {
    slug: "onboarding",
    file: "ONBOARDING.md",
    title: "Developer Onboarding",
    description:
      "Getting the project running locally, understanding the pipeline, and how each export is produced.",
  },
  {
    slug: "architecture",
    file: "architecture.md",
    title: "System Architecture",
    description:
      "How the FastAPI + pandas pipeline and Next.js frontend fit together across the five target systems.",
  },
  {
    slug: "automation-strategy",
    file: "AUTOMATION_STRATEGY.md",
    title: "Automation Strategy",
    description:
      "The rules for deciding what can be automated: APIs open the door, and everything else stays manual.",
  },
  {
    slug: "manual-process",
    file: "MANUAL_PROCESS.md",
    title: "Current Manual Process",
    description:
      "The manual Excel-based workflow this system replaces, kept as a reference and as a fallback.",
  },
  {
    slug: "changelog",
    file: "CHANGELOG.md",
    title: "Changelog",
    description: "A running record of what has changed in the project.",
  },
]

export function slugFromFile(file: string): string | undefined {
  const base = file.split(/[\\/]/).pop()?.replace(/\.md$/i, "") ?? ""
  const slug = base
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
  return slug ? slug : undefined
}

export function docBySlug(slug: string): DocMeta | undefined {
  return DOCS.find((doc) => doc.slug === slug)
}

export function docByFile(file: string): DocMeta | undefined {
  return DOCS.find((doc) => doc.file.toLowerCase() === file.toLowerCase())
}

export function rewriteDocLink(href: string): string {
  if (!href) return href
  const head = href.split("#")[0]
  const hash = href.slice(head.length)
  if (/^https?:\/\//i.test(head) || head.startsWith("/") || head === "") {
    return href
  }
  if (/\.md$/i.test(head)) {
    const target = docByFile(head)
    return target ? `/docs/${target.slug}${hash}` : href
  }
  return href
}
