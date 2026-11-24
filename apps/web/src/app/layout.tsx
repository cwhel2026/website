import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import "./globals.css";
import { ConsentBanner } from "@/components/site/consent-banner";
import { AttributionBootstrap } from "@/components/site/attribution-bootstrap";

const body = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  display: "swap",
});

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://website-production-c21e95cd.up.railway.app",
  ),
  title: {
    default: "Revive My Drive | Professional Driveway Restoration",
    template: "%s | Revive My Drive",
  },
  description:
    "Premium tarmac, block paving and imprinted concrete restoration across Lancashire, Merseyside and Greater Manchester. Instant provisional quotations online.",
  openGraph: {
    type: "website",
    locale: "en_GB",
    siteName: "Revive My Drive",
  },
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