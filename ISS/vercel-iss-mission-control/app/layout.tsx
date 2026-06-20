import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ISS Viewing Coach",
  description: "Live ISS tracker with a local viewing coach.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
