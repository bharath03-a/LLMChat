"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { FiUpload, FiX } from "react-icons/fi"
import ChatInterface from "@/components/chat-interface"
import { motion } from "framer-motion"

export default function DocumentPage() {
  const [file, setFile] = useState<File | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [selectedText, setSelectedText] = useState<string>("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (selectedFile.type === "application/pdf") {
        setFile(selectedFile)
        const url = URL.createObjectURL(selectedFile)
        setPdfUrl(url)
      } else {
        alert("Please upload a PDF file")
      }
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile)
        const url = URL.createObjectURL(droppedFile)
        setPdfUrl(url)
      } else {
        alert("Please upload a PDF file")
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const clearFile = () => {
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl)
    }
    setFile(null)
    setPdfUrl(null)
    setSelectedText("")
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleTextSelection = () => {
    const selection = window.getSelection()
    if (selection && selection.toString()) {
      setSelectedText(selection.toString())
    }
  }

  const handleSendMessage = async (message: string) => {
    // In a real application, this would send the message and selected text to an AI model
    // For now, we'll just return a placeholder response
    const response = selectedText
      ? `I see you've selected: "${selectedText}". Here's my analysis of your question: "${message}"`
      : `Here's my analysis of your question: "${message}"`

    // Clear the selected text after sending
    setSelectedText("")

    return response
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
        Document Analysis
      </motion.h1>

      <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-250px)]">
        <motion.div
          className="flex-1 h-full"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {!pdfUrl ? (
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg h-full flex flex-col items-center justify-center p-6"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <FiUpload className="text-4xl text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4 text-center">Drag and drop your PDF here, or click to browse</p>
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
                ref={fileInputRef}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-orange-500 text-white px-4 py-2 rounded-md hover:bg-orange-600 transition"
              >
                Upload PDF
              </button>
            </div>
          ) : (
            <div className="relative h-full">
              <button onClick={clearFile} className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md z-10">
                <FiX className="text-gray-600" />
              </button>
              <iframe
                src={`${pdfUrl}#toolbar=0`}
                className="w-full h-full rounded-lg border border-gray-300"
                onMouseUp={handleTextSelection}
              />
              {selectedText && (
                <div className="absolute bottom-4 left-4 right-4 bg-orange-100 border border-orange-300 rounded-md p-3 shadow-md">
                  <p className="text-sm text-gray-700">
                    <span className="font-semibold">Selected text:</span> {selectedText}
                  </p>
                </div>
              )}
            </div>
          )}
        </motion.div>

        <motion.div
          className="flex-1 h-full"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ChatInterface
            onSendMessage={handleSendMessage}
            placeholder={file ? "Ask about this document..." : "Upload a document to start chatting..."}
          />
        </motion.div>
      </div>
    </div>
  )
}
