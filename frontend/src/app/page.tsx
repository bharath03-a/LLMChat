import Intro from "@/components/intro";
import KeyFeatures from "@/components/keyfeatures";
import Image from "next/image";

export default function Home() {
  return (
    <main className="flex flex-col items-center px-2">
      <Intro/>
      <KeyFeatures/>
    </main>
  );
}
