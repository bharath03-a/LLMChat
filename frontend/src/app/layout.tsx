import type React from "react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import type { Metadata } from "next"
import { Geist, Geist_Mono, Lato } from "next/font/google"
import ActiveSectionContextProvider from "@/context/active-section-context"
import ThemeContextProvider from "@/context/theme-context"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const lato = Lato({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-lato",
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "LegalAI - Your AI-powered Legal Assistant",
  description: "Summarize cases, extract legal insights, and gain knowledge specific to your legal problems",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body
        className={`${lato.className} bg-gray-100 text-gray-800 relative min-h-screen flex flex-col pt-28 sm:pt-36`}
      >
        <div
          className="bg-orange-200 absolute top-[-6rem] -z-10 right-[11rem] h-[31.25rem] 
        w-[31.25rem] rounded-full blur-[10rem] sm:w-[68.75rem]"
        ></div>
        <div
          className="bg-orange-200 absolute top-[-1rem] -z-10 left-[35rem] h-[31.25rem] 
        w-[50rem] rounded-full blur-[10rem] sm:w-[68.75rem] md:left-[-33rem] 
        lg:left-[-28rem] xl:[left-[-15rem] 2xl:left-[-5rem]"
        ></div>
        <div
          className="bg-orange-200 absolute top-[-1rem] -z-10 right-[35rem] h-[31.25rem] 
        w-[50rem] rounded-full blur-[10rem] sm:w-[68.75rem] md:right-[-33rem] 
        lg:right-[-28rem] xl:right-[-15rem] 2xl:right-[-5rem]"
        ></div>

        <ThemeContextProvider>
          <ActiveSectionContextProvider>
            <Header />
            <div className="flex-grow">{children}</div>
            <Footer />
          </ActiveSectionContextProvider>
        </ThemeContextProvider>
      </body>
    </html>
  )
}


import './globals.css'