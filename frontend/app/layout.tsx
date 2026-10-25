import "@rainbow-me/rainbowkit/styles.css";
import "./globals.css";

import Web3Provider from "@/providers/Web3Provider";
import AppShell from "@/components/layout/AppShell";
import { AuthProvider } from "@/providers/AuthProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Web3Provider>
          <AuthProvider>
          <AppShell>{children}</AppShell>
          </AuthProvider>
        </Web3Provider>
      </body>
    </html>
  );
}
