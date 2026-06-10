import type { Metadata, Viewport } from "next";
import { Instrument_Serif } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const instrumentFont = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-instrument",
});

export const metadata: Metadata = {
  title: "VentureMind AI — AI Investment Committee",
  description:
    "Six AI agents debate your startup idea. Get a BUILD, CAUTION, or REJECT verdict with evidence in 90 seconds.",
  keywords: ["startup validation", "AI", "investment committee", "founder tools"],
  authors: [{ name: "VentureMind AI" }],
  openGraph: {
    title: "VentureMind AI — AI Investment Committee",
    description: "Know if your startup idea is worth building in 90 seconds.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "VentureMind AI",
    description: "AI Investment Committee — BUILD, CAUTION, or REJECT in 90 seconds.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#080a0e",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`dark ${instrumentFont.variable}`}
      suppressHydrationWarning
    >
      <body className="antialiased">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
