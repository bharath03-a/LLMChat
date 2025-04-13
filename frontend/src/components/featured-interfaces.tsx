"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { FiFileText, FiImage, FiMessageSquare } from "react-icons/fi"

const interfaces = [
  {
    icon: <FiFileText className="text-4xl text-orange-500" />,
    title: "Document Analysis",
    description: "Upload legal documents and PDFs to analyze, extract insights, and ask specific questions.",
    link: "/document",
    color: "bg-blue-50",
  },
  {
    icon: <FiImage className="text-4xl text-orange-500" />,
    title: "Image Analysis",
    description: "Upload images of legal documents, evidence, or scenes for AI-powered visual analysis.",
    link: "/image",
    color: "bg-green-50",
  },
  {
    icon: <FiMessageSquare className="text-4xl text-orange-500" />,
    title: "Legal Chat",
    description: "Chat directly with our AI legal assistant about any legal questions or concerns.",
    link: "/chat",
    color: "bg-purple-50",
  },
]

export default function FeaturedInterfaces() {
  return (
    <section className="w-full max-w-7xl mx-auto py-16 px-6">
      <motion.h2
        className="text-center text-3xl sm:text-4xl font-semibold text-gray-700 mb-12"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        Explore Our Interfaces
      </motion.h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {interfaces.map((item, index) => (
          <motion.div
            key={index}
            className="rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-shadow"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
          >
            <Link href={item.link} className="block h-full">
              <div className={`${item.color} p-8 h-full flex flex-col`}>
                <div className="mb-4">{item.icon}</div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{item.title}</h3>
                <p className="text-gray-600 mb-6 flex-grow">{item.description}</p>
                <div className="mt-auto">
                  <span className="inline-flex items-center gap-2 text-orange-500 font-medium">
                    Try Now
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M5 12h14"></path>
                      <path d="m12 5 7 7-7 7"></path>
                    </svg>
                  </span>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
