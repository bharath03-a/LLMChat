import Link from "next/link"
import { FiBookOpen } from "react-icons/fi"

export default function Logo({ className = "" }: { className?: string }) {
  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <div className="bg-orange-500 text-white p-1.5 rounded-md">
        <FiBookOpen size={18} />
      </div>
      <span className="font-bold text-gray-800 text-lg">LegalAI</span>
    </Link>
  )
}
