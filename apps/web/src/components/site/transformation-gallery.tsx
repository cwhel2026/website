"use client";

import { useState } from "react";
import { BeforeAfterSlider } from "@/components/site/before-after-slider";
import { MEDIA, type MediaAsset } from "@/lib/media-assets";

export type TransformationExample = {
  id: string;
  title: string;
  before: MediaAsset;
  after: MediaAsset;
  caption: string;
};

export const TRANSFORMATION_EXAMPLES: TransformationExample[] = [
  {
    id: "tarmac-reference",
    title: "Tarmac colour and contrast",
    before: MEDIA.beforeAfter.before,
    after: MEDIA.beforeAfter.after,
    caption: MEDIA.beforeAfter.caption,
  },
];

export function TransformationGallery({ examples = TRANSFORMATION_EXAMPLES }: { examples?: TransformationExample[] }) {
  const [active, setActive] = useState(0);
  const example = examples[Math.min(active, examples.length - 1)];
  if (!example) return null;

  return (
    <div>
      {examples.length > 1 ? (
        <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Restoration examples">
          {examples.map((item, index) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={index === active}
              className={`min-h-11 border px-4 text-sm font-semibold ${
                index === active ? "border-brand-ink bg-brand-ink text-white" : "border-brand-line bg-white text-brand-ink"
              }`}
              onClick={() => setActive(index)}
            >
              {item.title}
            </button>
          ))}
        </div>
      ) : null}
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-brand-ink">
        Illustrative transformation
      </p>
      <BeforeAfterSlider before={example.before} after={example.after} caption={example.caption} />
      <p className="mt-3 text-sm leading-relaxed text-brand-ink/70">
        Further examples will be added when a driveway is photographed before and after from the same position.
        Generated images are not shown as customer work.
      </p>
    </div>
  );
}
