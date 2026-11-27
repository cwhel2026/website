"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const KEY = "rmd_analytics_consent";

export function ConsentBanner() {
  const pathname = usePathname();
  const [show, setShow] = useState(false);
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!localStorage.getItem(KEY)) setShow(true);
  }, []);

  useEffect(() => {
    const node = panel.current;
    if (!show || !node || pathname?.startsWith("/dashboard")) {
      document.documentElement.style.setProperty("--consent-offset", "0px");
      return;
    }
    const apply = () => {
      document.documentElement.style.setProperty("--consent-offset", `${node.offsetHeight}px`);
    };
    apply();
    const observer = new ResizeObserver(apply);
    observer.observe(node);
    return () => {
      observer.disconnect();
      document.documentElement.style.setProperty("--consent-offset", "0px");
    };
  }, [show, pathname]);

  if (!show || pathname?.startsWith("/dashboard")) return null;

  return (
    <div
      ref={panel}
      role="dialog"
      aria-label="Cookie consent"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-brand-line bg-white px-4 pt-4 shadow-[0_-8px_24px_rgba(21,21,21,0.08)]"
      style={{ paddingBottom: "calc(1rem + env(safe-area-inset-bottom))" }}
    >
      <div className="site-container flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-2xl text-sm leading-relaxed text-brand-ink/80">
          Essential cookies keep your quotation on this device. Analytics cookies are optional and stay off until
          you allow them. See our privacy policy.
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
