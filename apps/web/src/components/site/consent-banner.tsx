"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const KEY = "rmd_analytics_consent";

export function ConsentBanner() {
  const pathname = usePathname();
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(KEY)) setShow(true);
  }, []);

  // The admin portal sets no analytics cookies, and the banner would cover its bottom navigation.
  if (!show || pathname?.startsWith("/dashboard")) return null;

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-stone-line bg-white p-4 shadow-lift"
    >
      <div className="site-container flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-2xl text-sm text-asphalt/80">
          We use essential cookies for quotations and optional analytics to understand how visitors
          find us. You can accept analytics or continue with essential only. See our privacy policy.
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            className="btn-secondary px-4 py-2"
            onClick={() => {
              localStorage.setItem(KEY, "essential");
              setShow(false);
            }}
          >
            Essential only
          </button>
          <button
            type="button"
            className="btn-primary px-4 py-2"
            onClick={() => {
              localStorage.setItem(KEY, "granted");
              setShow(false);
            }}
          >
            Accept analytics
          </button>
        </div>
      </div>
    </div>
  );
}