"use client";

import { useState } from "react";
import { BeforeAfterSlider } from "@/components/site/before-after-slider";
import { RESTORATION_PAIRS, type RestorationPair } from "@/lib/media-assets";

export type TransformationExample = RestorationPair;

export const TRANSFORMATION_EXAMPLES: TransformationExample[] = RESTORATION_PAIRS;

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
      <BeforeAfterSlider before={example.before} after={example.after} caption={example.caption} />
    </div>
  );
}
