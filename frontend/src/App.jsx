import { useState } from 'react'
import { cn } from "@/utils"

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="p-8 border rounded-lg shadow-lg bg-card text-card-foreground">
        <h1 className="text-3xl font-bold mb-4">Chitragupta Dashboard</h1>
        <p className="text-muted-foreground">Frontend initialized successfully with Tailwind CSS.</p>
        <button className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90">
          Get Started
        </button>
      </div>
    </div>
  )
}

export default App
