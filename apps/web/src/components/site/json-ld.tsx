import { publicBrand } from "@/lib/public-brand";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://website-production-c21e95cd.up.railway.app";

export function BusinessJsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": "HomeAndConstructionBusiness",
    name: publicBrand.legalName,
    slogan: publicBrand.tagline,
    url: siteUrl,
    image: `${siteUrl}/media/approved/tarmac-approach-after.webp`,
    description: `Driveway and surface restoration across ${publicBrand.coverageAreas}. Instant estimates for tarmac restoration.`,
    areaServed: publicBrand.counties.map((name) => ({
      "@type": "AdministrativeArea",
      name,
    })),
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />
  );
}
