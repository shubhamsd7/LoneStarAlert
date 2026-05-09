import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "TxAlert",
  description: "Public Texas court record monitoring for civil lawsuit alerts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#18181B",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "#F8FAFC",
            },
          }}
        />
      </body>
    </html>
  );
}
