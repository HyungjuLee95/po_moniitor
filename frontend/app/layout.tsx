import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PO Monitor Main | SAP PO Operations",
  description: "SAP PO 서버, 채널, 메시지, 장애와 Collector를 통합 관리하는 내부 운영 콘솔",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
