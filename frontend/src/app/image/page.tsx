"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { FiUpload, FiX } from "react-icons/fi"
import ChatInterface from "@/components/chat-interface"
import { motion } from "framer-motion"

export default function ImagePage() {

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])
  
  const [file, setFile] = useState<File | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (selectedFile.type.startsWith("image/")) {
        setFile(selectedFile)
        const url = URL.createObjectURL(selectedFile)
        setImageUrl(url)
      } else {
        alert("Please upload an image file")
      }
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type.startsWith("image/")) {
        setFile(droppedFile)
        const url = URL.createObjectURL(droppedFile)
        setImageUrl(url)
      } else {
        alert("Please upload an image file")
      }
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const clearFile = () => {
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl)
    }
    setFile(null)
    setImageUrl(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleSendMessage = async (message: string) => {
    // In a real application, this would send the message and image to an AI model
    // For now, we'll just return a placeholder response
    return `I've analyzed the image you uploaded. Regarding your question: "${message}", here's what I found...`
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.h1
        className="text-3xl font-bold text-center mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Image Analysis
      </motion.h1>

      <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-250px)]">
        <motion.div
          className="flex-1 h-full"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {!imageUrl ? (
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg h-full flex flex-col items-center justify-center p-6"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <FiUpload className="text-4xl text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4 text-center">Drag and drop your image here, or click to browse</p>
              <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" ref={fileInputRef} />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-orange-500 text-white px-4 py-2 rounded-md hover:bg-orange-600 transition"
              >
                Upload Image
              </button>
            </div>
          ) : (
            <div className="relative h-full flex items-center justify-center bg-gray-100 rounded-lg">
              <button onClick={clearFile} className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md z-10">
                <FiX className="text-gray-600" />
              </button>
              <div className="relative max-h-full max-w-full p-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imageUrl || "/placeholder.svg"}
                  alt="Uploaded image"
                  className="max-h-[calc(100vh-300px)] max-w-full object-contain rounded-lg shadow-md"
                />
              </div>
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
            placeholder={file ? "Ask about this image..." : "Upload an image to start chatting..."}
          />
        </motion.div>
      </div>
    </div>
  )
}
