"use client";

import { useCallback, useRef, useState } from "react";

type Props = {
  beforeLabel?: string;
  afterLabel?: string;
  caption: string;
};

export function BeforeAfterSlider({
  beforeLabel = "Before (illustrative)",
  afterLabel = "After (illustrative)",
  caption,
}: Props) {
  const [pct, setPct] = useState(50);
  const dragging = useRef(false);

  const move = useCallback((clientX: number, rect: DOMRect) => {
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    setPct((x / rect.width) * 100);
  }, []);

  return (
    <figure className="space-y-3">
      <div
        className="relative aspect-[16/10] w-full cursor-col-resize select-none overflow-hidden rounded-lg border border-stone-line bg-asphalt-950"
        onPointerDown={(e) => {
          dragging.current = true;
          (e.target as HTMLElement).setPointerCapture(e.pointerId);
          move(e.clientX, e.currentTarget.getBoundingClientRect());
        }}
        onPointerMove={(e) => {
          if (!dragging.current) return;
          move(e.clientX, e.currentTarget.getBoundingClientRect());
        }}
        onPointerUp={() => {
          dragging.current = false;
        }}
      >
        <div
          className="absolute inset-0 bg-gradient-to-br from-zinc-600 to-zinc-800"
          aria-hidden
        />
        <div
          className="absolute inset-0 bg-gradient-to-br from-restore-muted via-restore-green/40 to-restore-dark/80"
          style={{ clipPath: `inset(0 ${100 - pct}% 0 0)` }}
          aria-hidden
        />
        <div
          className="absolute bottom-0 left-0 top-0 w-0.5 bg-white shadow-lg"
          style={{ left: `${pct}%` }}
          aria-hidden
        />
        <span className="absolute left-3 top-3 rounded bg-black/50 px-2 py-1 text-xs text-white">
          {beforeLabel}
        </span>
        <span className="absolute right-3 top-3 rounded bg-restore-dark/80 px-2 py-1 text-xs text-white">
          {afterLabel}
        </span>
      </div>
      <figcaption className="text-center text-sm text-asphalt/70">{caption}</figcaption>
    </figure>
  );
}