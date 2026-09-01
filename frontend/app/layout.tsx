import "@rainbow-me/rainbowkit/styles.css";
import "./globals.css";

import Web3Provider from "@/providers/Web3Provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Web3Provider>
          {children}
        </Web3Provider>
      </body>
    </html>
  );
}