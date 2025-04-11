"use client";

import { BsArrowRight } from "react-icons/bs";
import { FiBarChart2, FiMessageSquare, FiFileText, FiImage } from "react-icons/fi";
import { motion } from "framer-motion";

const features = [
  {
    icon: <FiBarChart2 className="text-3xl text-orange-500" />,
    title: "Interactive Dashboard",
    desc: "View real-time metrics and analytics from your data sources.",
  },
  {
    icon: <FiMessageSquare className="text-3xl text-orange-500" />,
    title: "AI Chat Interface",
    desc: "Engage with our advanced AI assistant for instant help and information.",
  },
  {
    icon: <FiFileText className="text-3xl text-orange-500" />,
    title: "Document Analysis",
    desc: "Upload PDFs and ask specific questions about their content.",
  },
  {
    icon: <FiImage className="text-3xl text-orange-500" />,
    title: "Image Analysis",
    desc: "Upload images and chat with AI about their content and details.",
  },
];

function KeyFeatures() {
  return (
    <section className="py-16 px-6">
        <motion.h2
            className="text-center text-3xl sm:text-4xl font-semibold text-gray-700 mb-12"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            Key Features
        </motion.h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
            {features.map((feature, idx) => (
            <motion.div
                key={idx}
                className="border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition bg-white flex flex-col justify-between"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, ease: "easeInOut" }}
            >
                <div className="mb-6">
                    {feature.icon}
                    <h3 className="mt-4 font-semibold text-lg text-gray-700">{feature.title}</h3>
                    <p className="mt-2 text-gray-500 text-sm">{feature.desc}</p>
                </div>

            <button className="mt-auto inline-flex items-center gap-2 border border-gray-400 rounded-md px-4 py-2 text-sm text-gray-800 hover:bg-gray-100 transition">
              Explore <BsArrowRight />
            </button>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

export default KeyFeatures