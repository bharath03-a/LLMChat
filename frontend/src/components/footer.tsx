import { FiGithub, FiTwitter, FiLinkedin } from "react-icons/fi"
import Logo from "./logo"

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center">
          <Logo className="mb-4" />
          <p className="text-gray-500 max-w-md mb-6">
            Your AI-powered legal assistant. Summarize cases, extract insights, and get answers to your legal questions.
          </p>
          <div className="flex space-x-4 mb-6">
            <a href="#" className="text-gray-400 hover:text-gray-500">
              <span className="sr-only">Twitter</span>
              <FiTwitter className="h-6 w-6" />
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-500">
              <span className="sr-only">GitHub</span>
              <FiGithub className="h-6 w-6" />
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-500">
              <span className="sr-only">LinkedIn</span>
              <FiLinkedin className="h-6 w-6" />
            </a>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-200 pt-8">
          <p className="text-base text-gray-400 text-center">
            &copy; {new Date().getFullYear()} LegalAI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
