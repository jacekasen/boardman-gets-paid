import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Board Man Gets Paid — The value beyond the contract",
  description:
    "Explore NBA contract value, team payrolls, and apron-aware trades using the Board Man valuation engine.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
