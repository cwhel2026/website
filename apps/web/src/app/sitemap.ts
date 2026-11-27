import type { MetadataRoute } from "next";

const base = process.env.NEXT_PUBLIC_SITE_URL ?? "https://website-production-c21e95cd.up.railway.app";

const paths = [
  "",
  "/quote",
  "/services",
  "/services/tarmac-restoration",
  "/services/block-paving",
  "/services/imprinted-concrete",
  "/services/commercial-car-parks",
  "/services/minor-repairs",
  "/services/commercial-restoration",
  "/commercial",
  "/service-areas",
  "/transformations",
  "/how-it-works",
  "/gallery",
  "/faq",
  "/contact",
  "/privacy",
  "/terms",
  "/areas/tarmac-restoration-blackpool",
  "/areas/driveway-restoration-liverpool",
  "/areas/tarmac-restoration-manchester",
  "/areas/driveway-restoration-southport",
  "/areas/tarmac-restoration-preston",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return paths.map((path) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : 0.7,
  }));
}