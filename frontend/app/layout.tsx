import "./globals.css";
import type { Metadata } from "next";
import { Toaster } from "@/components/ui/toast";
import { CartDrawer } from "@/components/cart-drawer";
import { AuthWrapper } from "@/components/auth-wrapper";

export const metadata: Metadata = {
  title: "AURA BELL — Shop Beyond Limits",
  description: "Experience the Grand Luxury Multi-Store Virtual Marketplace at Aura Bell",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;800;900&family=Cormorant+Garamond:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-screen bg-background text-foreground font-sans antialiased selection:bg-gold-500/30 selection:text-gold-200"
        style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
      >
        <AuthWrapper>
          {children}
          <CartDrawer />
          <Toaster />
        </AuthWrapper>
      </body>
    </html>
  );
}
