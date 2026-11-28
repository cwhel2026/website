"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import { apiGet } from "@/lib/api";
import { ApiError } from "@/lib/api-errors";
import { clearToken, getToken } from "@/lib/auth-client";
import { brand } from "@/lib/brand";
import { onLoadError, type LoadErrorEvent } from "@/lib/load-errors";
import { BOTTOM_NAV, isNavActive, NAV_SECTIONS } from "@/lib/portal-nav";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [navSearch, setNavSearch] = useState("");
  const currentSection = NAV_SECTIONS.flatMap(s => s.items).filter(i => isNavActive(pathname, i.href)).sort((a,b) => b.href.length-a.href.length)[0];
  useEffect(() => {
    if (!drawerOpen) return;
    const close = (e: KeyboardEvent) => { if (e.key === 'Escape') setDrawerOpen(false); };
    document.addEventListener('keydown', close);
    const old = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', close); document.body.style.overflow = old; };
  }, [drawerOpen]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loadErrors, setLoadErrors] = useState<LoadErrorEvent[]>([]);

  useEffect(() => {
    setDrawerOpen(false);
    setNavSearch("");
    setLoadErrors([]);
  }, [pathname]);

  useEffect(
    () =>
      onLoadError((e) =>
        setLoadErrors((prev) => (prev.some((p) => p.path === e.path) ? prev : [...prev, e].slice(-5))),
      ),
    [],
  );

  useEffect(() => {
    if (pathname === "/dashboard/login" || pathname.startsWith("/dashboard/login/")) {
      setReady(true);
      return;
    }
    const token = getToken();
    if (!token) {
      router.replace("/dashboard/login");
      return;
    }
    apiGet<{ email?: string }>("/api/v1/auth/me", token)
      .then(() => setReady(true))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status !== 401) {
          setReady(true);
          return;
        }
        clearToken();
        router.replace("/dashboard/login");
      });
  }, [pathname, router]);

  if (pathname === "/dashboard/login" || pathname.startsWith("/dashboard/login/")) {
    return <>{children}</>;
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1a1a1a] text-white/80">
        <p className="text-sm">Loading {brand.portalTitle}…</p>
      </div>
    );
  }

  const inMarketing = pathname.startsWith("/dashboard/marketing");
  // Pages not yet migrated to the dark portal components use light-theme text colours.
  const darkNative = inMarketing || pathname === "/dashboard" || pathname === "/dashboard/launch-readiness" || pathname === "/dashboard/approvals";

  return (
    <div className="portal-root min-h-screen bg-[#141716] text-white overflow-x-hidden">
      <a href="#portal-main" className="sr-only focus:not-sr-only focus:fixed focus:z-[70] focus:bg-amber-300 focus:p-3 focus:text-black">Skip to content</a>
      <header
        className="sticky top-0 z-40 border-b border-white/10 bg-[#1a1a1a]/95 backdrop-blur md:pl-0"
        style={{ paddingTop: "max(0.5rem, env(safe-area-inset-top))" }}
      >
        <div className="flex h-12 max-w-[1440px] items-center justify-between gap-3 px-4 md:mx-auto">
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold uppercase tracking-[0.18em] text-[#eab308]">
              {brand.legalName}
            </p>
            <p className="truncate text-sm font-medium text-white/90">{currentSection?.label ?? brand.portalTitle}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              className="hidden rounded-lg p-2 text-white/70 hover:bg-white/10 md:inline-flex"
              onClick={() => setSidebarCollapsed((c) => !c)}
              aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
            </button>
            <button
              type="button"
              className="rounded-lg p-2 text-white/70 hover:bg-white/10"
              onClick={async () => {
                await clearToken();
                router.push("/dashboard/login");
              }}
              aria-label="Sign out"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1440px]">
        <aside
          className={`hidden shrink-0 border-r border-white/10 md:block ${
            sidebarCollapsed ? "w-[4.25rem]" : "w-56"
          }`}
        >
          <nav className="sticky top-14 max-h-[calc(100vh-3.5rem)] overflow-y-auto px-2 py-4 text-sm">
            {NAV_SECTIONS.map((section) => (
              <div key={section.id} className="mb-4">
                {!sidebarCollapsed && (
                  <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wide text-white/45">
                    {section.title}
                  </p>
                )}
                <ul className="space-y-0.5">
                  {section.items.map((item) => {
                    const active = currentSection?.href === item.href;
                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          title={item.label}
                          aria-current={active ? "page" : undefined}
                          className={`block rounded-lg px-2 py-2 ${
                            active
                              ? "bg-[#eab308] font-semibold text-[#1a1a1a]"
                              : "text-white/75 hover:bg-white/10"
                          } ${item.legacy ? "opacity-60" : ""} ${sidebarCollapsed ? "text-center text-xs" : ""}`}
                        >
                          {sidebarCollapsed ? item.label.charAt(0) : item.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        </aside>

        <main id="portal-main" className="min-w-0 flex-1 px-3 sm:px-6 py-5 pb-[calc(5rem+env(safe-area-inset-bottom))] md:pb-6">
          <div
            className={`mx-auto max-w-full ${
              inMarketing
                ? "text-white"
                : darkNative
                  ? "rounded-3xl text-white"
                  : "portal-legacy overflow-x-auto rounded-2xl border border-white/10 bg-[#f8faf9] p-4 text-[#1a1a1a] shadow-lg md:p-6"
            }`}
          >
            {loadErrors.length > 0 && (
              <div
                role="alert"
                data-testid="load-error-banner"
                className="mb-4 rounded-lg border border-red-500/50 bg-red-950/80 px-3 py-2 text-sm text-red-50"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="font-semibold">
                    Some data on this page failed to load — anything shown as empty below may not be accurate.
                  </p>
                  <button
                    type="button"
                    onClick={() => setLoadErrors([])}
                    className="shrink-0 rounded p-1 text-red-100 hover:bg-white/10"
                    aria-label="Dismiss"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <ul className="mt-1 space-y-0.5 text-xs text-red-100/90">
                  {loadErrors.map((e) => (
                    <li key={e.path} className="break-all">
                      {e.path.replace(/^\/api\/v1/, "")}: {e.status ? `HTTP ${e.status} — ` : ""}
                      {e.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {children}
          </div>
        </main>
      </div>

      <nav
        className="fixed bottom-0 left-0 right-0 z-50 border-t border-amber-300/15 bg-[#191d1b]/95 backdrop-blur-xl md:hidden"
        style={{ paddingBottom: "max(0.35rem, env(safe-area-inset-bottom))" }}
        aria-label="Primary"
      >
        <ul className="mx-auto flex max-w-lg items-stretch justify-around px-1 pt-1">
          {BOTTOM_NAV.map((item) => {
            const Icon = item.icon;
            const isMore = item.href === "#more";
            const active = !isMore && isNavActive(pathname, item.href, item.matchPrefix);
            if (isMore) {
              return (
                <li key="more">
                  <button
                    type="button"
                    aria-expanded={drawerOpen}
                    aria-controls="portal-menu"
                    onClick={() => setDrawerOpen(true)}
                    className="flex min-h-[48px] min-w-[56px] flex-col items-center justify-center gap-0.5 px-2 text-[10px] text-white/70"
                  >
                    <Icon className="h-5 w-5" />
                    <span>More</span>
                  </button>
                </li>
              );
            }
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex min-h-[48px] min-w-[56px] flex-col items-center justify-center gap-0.5 px-2 text-[10px] ${
                    active ? "rounded-xl bg-amber-300/10 font-semibold text-[#eab308]" : "text-white/70"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {drawerOpen && (
        <div className="fixed inset-0 z-[60] md:hidden" id="portal-menu" role="dialog" aria-modal="true" aria-label="Menu">
          <button
            type="button"
            className="absolute inset-0 bg-black/60"
            aria-label="Close menu"
            onClick={() => setDrawerOpen(false)}
          />
          <div
            className="absolute bottom-0 left-0 right-0 max-h-[85dvh] overflow-y-auto rounded-t-3xl border-t border-white/10 bg-[#1a1a1a] px-4 pt-3"
            style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
          >
            <div className="mb-3 flex items-center justify-between">
              <p className="text-lg font-semibold text-white">All areas</p>
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close navigation"
                className="rounded-lg p-2 text-white/70 hover:bg-white/10"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <input autoFocus aria-label="Find a department" placeholder="Find a department…" value={navSearch} onChange={e => setNavSearch(e.target.value)} className="mb-3 w-full rounded-lg border border-white/20 bg-black/20 p-3 text-base text-white" />
            {NAV_SECTIONS.filter(section => section.items.some(item => item.label.toLowerCase().includes(navSearch.toLowerCase()))).map((section) => (
              <details key={section.id} className="border-b border-white/10 py-2" open={!!navSearch || section.id === "overview"}>
                <summary className="cursor-pointer list-none py-2 text-sm font-medium text-[#eab308]">
                  {section.title}
                </summary>
                <ul className="pb-2 pl-1">
                  {section.items.filter(item => item.label.toLowerCase().includes(navSearch.toLowerCase())).map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={`block rounded-lg px-3 py-2.5 text-sm ${
                          isNavActive(pathname, item.href)
                            ? "bg-[#eab308]/20 font-medium text-[#eab308]"
                            : "text-white/85"
                        }`}
                      >
                        {item.label}
                        {item.legacy ? <span className="ml-1 text-xs text-white/40">(legacy)</span> : null}
                      </Link>
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}