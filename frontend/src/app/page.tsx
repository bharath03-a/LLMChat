import Intro from "@/components/intro"
import KeyFeatures from "@/components/keyfeatures"

export default function Home() {
  return (
    <main className="flex flex-col items-center px-2">
      <Intro />
      <KeyFeatures />
    </main>
  )
}
