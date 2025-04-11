"use client";

import React from 'react'
import { motion } from 'framer-motion';
import { BsArrowRight } from 'react-icons/bs';
import Link from 'next/link';

function Intro() {
  return (
    <section className="min-h-[60vh] flex flex-col items-center justify-center text-center px-6">
        <motion.h1
            className="text-4xl sm:text-5xl font-bold text-gray-700 mb-4"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            Meet Your AI-powered Legal Assistant
        </motion.h1>

        <motion.p
            className="text-lg sm:text-xl text-gray-500 max-w-2xl mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            Summarize cases, extract legal insights, gain knowledge specific to your case or problem – all with one intelligent assistant.
        </motion.p>

        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            <Link 
                href="#get-started"
                className="bg-orange-500 text-white text-lg px-6 py-3 rounded-md font-semibold hover:bg-orange-600 transition flex items-center gap-2"
            >
                Try It Now <BsArrowRight className="text-xl" />
            </Link>
        </motion.div>
    </section>
  )
}

export default Intro