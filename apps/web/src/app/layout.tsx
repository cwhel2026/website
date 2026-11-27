import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { ConsentBanner } from "@/components/site/consent-banner";
import { AttributionBootstrap } from "@/components/site/attribution-bootstrap";
import { publicBrand } from "@/lib/public-brand";

const body = localFont({
  src: "../fonts/outfit-latin.woff2",
  variable: "--font-body",
  display: "swap",
  weight: "400 600",
});

const display = localFont({
  src: "../fonts/newsreader-latin.woff2",
  variable: "--font-display",
  display: "swap",
  weight: "400 600",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://website-production-c21e95cd.up.railway.app",
  ),
  title: {
    default: `${publicBrand.tradingName} | ${publicBrand.tagline}`,
    template: `%s | ${publicBrand.tradingName}`,
  },
  description: `Driveway and surface restoration across ${publicBrand.coverageAreas}. Instant estimates for tarmac restoration. ${publicBrand.tagline}`,
  alternates: { canonical: "./" },
  openGraph: {
    type: "website",
    locale: "en_GB",
    siteName: publicBrand.legalName,
    images: [
      {
        url: "/media/approved/hero-home.webp",
        alt: "UK residential tarmac driveway used as a reference photograph",
      },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#151515",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-GB">
      <body className={`${body.variable} ${display.variable} antialiased font-sans`}>
        <AttributionBootstrap />
        {children}
        <ConsentBanner />
      </body>
    </html>
  );
}