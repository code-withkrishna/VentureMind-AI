import type { Metadata, Viewport } from "next";
import { Instrument_Serif } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import PendoInitializer from "@/components/PendoInitializer";

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
      <head>
        <Script id="pendo-install" strategy="afterInteractive">{`
(function(apiKey){
    (function(p,e,n,d,o){var v,w,x,y,z;o=p[d]=p[d]||{};o._q=o._q||[];
    v=['initialize','identify','updateOptions','pageLoad','track','trackAgent'];for(w=0,x=v.length;w<x;++w)(function(m){
    o[m]=o[m]||function(){o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));};})(v[w]);
    y=e.createElement(n);y.async=!0;y.src='https://cdn.pendo.io/agent/static/'+apiKey+'/pendo.js';
    z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);})(window,document,'script','pendo');
})('91b9c4d0-d829-4ad1-8d37-d99903bdfce2');
`}</Script>
      </head>
      <body className="antialiased">
        <PendoInitializer />
        {children}
        <Toaster />
      </body>
    </html>
  );
}
