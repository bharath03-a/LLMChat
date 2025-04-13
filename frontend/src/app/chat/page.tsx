"use client"

import { useEffect } from "react"
import { motion } from "framer-motion"
import ChatInterface from "@/components/chat-interface"

export default function ChatPage() {
  const handleSendMessage = async (message: string) => {
    return `As your legal assistant, I can help with your question: "${message}". Here's my analysis...`
  }

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.h1
        className="text-3xl font-bold text-center mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Legal Chat Assistant
      </motion.h1>

      <motion.div
        className="max-w-4xl mx-auto h-[calc(100vh-200px)]"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <ChatInterface
          onSendMessage={handleSendMessage}
          placeholder="Ask any legal question..."
          initialMessages={[
            {
              id: "welcome",
              content: "Hello! I'm your AI legal assistant. How can I help you today?",
              role: "assistant",
              timestamp: new Date(),
            },
          ]}
        />
      </motion.div>
    </div>
  )
}
