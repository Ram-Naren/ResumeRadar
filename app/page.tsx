"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, Target, CheckCircle, AlertCircle, Loader2 } from "lucide-react"

interface AnalysisResult {
  score: number
  out_of: number
  suggestions: string[]
}

export default function ResumeAnalyzer() {
  const [resumeText, setResumeText] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [error, setError] = useState("")

  // Change this line:
  const API_BASE_URL = "https://resumeradar-5v6x.onrender.com"
  // or wherever you've deployed your FastAPI backend

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith(".pdf")) {
      setError("Please upload a PDF file")
      return
    }

    setIsExtracting(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch(`${API_BASE_URL}/extract-text`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to extract text from PDF")
      }

      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }

      setResumeText(data.text)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract text from PDF")
    } finally {
      setIsExtracting(false)
    }
  }

  const handleAnalyze = async () => {
    if (!resumeText.trim()) {
      setError("Please provide resume text")
      return
    }

    setIsAnalyzing(true)
    setError("")
    setAnalysisResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resume: resumeText,
          jd: jobDescription,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to analyze resume")
      }

      const data = await response.json()
      setAnalysisResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze resume")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "Excellent"
    if (score >= 60) return "Good"
    if (score >= 40) return "Fair"
    return "Needs Improvement"
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Enhanced Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        {/* Animated gradient orbs */}
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>

        {/* Geometric patterns */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-20 h-20 border-2 border-blue-400 rotate-45"></div>
          <div className="absolute top-40 right-20 w-16 h-16 border-2 border-purple-400 rotate-12"></div>
          <div className="absolute bottom-40 left-1/4 w-12 h-12 border-2 border-indigo-400 rotate-45"></div>
          <div className="absolute bottom-20 right-1/3 w-24 h-24 border-2 border-pink-400 rotate-12"></div>
        </div>

        {/* Floating dots pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-1/4 w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-3 h-3 bg-purple-400 rounded-full animate-pulse animation-delay-1000"></div>
          <div className="absolute bottom-1/3 left-1/3 w-2 h-2 bg-indigo-400 rounded-full animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-20 right-20 w-4 h-4 bg-pink-400 rounded-full animate-pulse animation-delay-3000"></div>
          <div className="absolute top-1/2 left-10 w-2 h-2 bg-yellow-400 rounded-full animate-pulse animation-delay-4000"></div>
        </div>

        {/* Grid pattern overlay */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(99, 102, 241, 0.3) 1px, transparent 0)`,
            backgroundSize: "40px 40px",
          }}
        ></div>
      </div>

      {/* Content with backdrop blur */}
      <div className="relative z-10 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto space-y-8 p-4">
          {/* Enhanced Header */}
          <div className="text-center space-y-6 py-12">
            <div className="relative">
              <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Resume Radar
              </h1>
              <div className="absolute -top-2 -left-2 w-4 h-4 bg-blue-400 rounded-full animate-ping opacity-75"></div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-400 rounded-full animate-ping opacity-75 animation-delay-1000"></div>
            </div>
            <p className="text-xl text-gray-700 max-w-3xl mx-auto leading-relaxed">
              Get instant feedback on your resume with AI-powered analysis. Upload your resume and job description to
              receive a comprehensive score and actionable suggestions.
            </p>
            <div className="flex justify-center space-x-4">
              <div className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full text-sm text-gray-600 border border-white/30">
                ✨ AI-Powered Analysis
              </div>
              <div className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full text-sm text-gray-600 border border-white/30">
                📊 Instant Results
              </div>
              <div className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full text-sm text-gray-600 border border-white/30">
                🎯 ATS Optimized
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Input Section */}
            <div className="space-y-6">
              {/* File Upload */}
              <Card className="card-enhanced">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Resume
                  </CardTitle>
                  <CardDescription>Upload a PDF file or paste your resume text below</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <Input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" id="file-upload" />
                    <Label htmlFor="file-upload" className="cursor-pointer">
                      <div className="space-y-2">
                        <FileText className="h-8 w-8 mx-auto text-gray-400" />
                        <div className="text-sm text-gray-600">
                          {isExtracting ? (
                            <div className="flex items-center justify-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Extracting text...
                            </div>
                          ) : (
                            "Click to upload PDF or drag and drop"
                          )}
                        </div>
                      </div>
                    </Label>
                  </div>
                </CardContent>
              </Card>

              {/* Resume Text */}
              <Card className="card-enhanced">
                <CardHeader>
                  <CardTitle>Resume Text</CardTitle>
                  <CardDescription>Paste your resume text here or upload a PDF above</CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    placeholder="Paste your resume text here..."
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    className="min-h-[200px] resize-none"
                  />
                </CardContent>
              </Card>

              {/* Job Description */}
              <Card className="card-enhanced">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Job Description (Optional)
                  </CardTitle>
                  <CardDescription>Add the job description to get tailored analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    placeholder="Paste the job description here for better analysis..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    className="min-h-[150px] resize-none"
                  />
                </CardContent>
              </Card>

              {/* Analyze Button */}
              <Button
                onClick={handleAnalyze}
                disabled={isAnalyzing || !resumeText.trim()}
                className="w-full h-12 text-lg"
                size="lg"
              >
                {isAnalyzing ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Analyzing Resume...
                  </div>
                ) : (
                  "Analyze Resume"
                )}
              </Button>
            </div>

            {/* Results Section */}
            <div className="space-y-6">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {analysisResult && (
                <>
                  {/* Score Card */}
                  <Card className="card-enhanced">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5" />
                        Analysis Results
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="text-center space-y-4">
                        <div className="space-y-2">
                          <div className={`text-6xl font-bold ${getScoreColor(analysisResult.score)}`}>
                            {analysisResult.score}
                          </div>
                          <div className="text-gray-600">out of {analysisResult.out_of}</div>
                          <Badge
                            variant={
                              analysisResult.score >= 80
                                ? "default"
                                : analysisResult.score >= 60
                                  ? "secondary"
                                  : "destructive"
                            }
                            className="text-sm px-3 py-1"
                          >
                            {getScoreLabel(analysisResult.score)}
                          </Badge>
                        </div>
                        <Progress value={(analysisResult.score / analysisResult.out_of) * 100} className="h-3" />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Suggestions Card */}
                  {analysisResult.suggestions.length > 0 && (
                    <Card className="card-enhanced">
                      <CardHeader>
                        <CardTitle>Suggestions for Improvement</CardTitle>
                        <CardDescription>Here are some recommendations to enhance your resume</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {analysisResult.suggestions.map((suggestion, index) => (
                            <div key={index} className="flex gap-3">
                              <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                                {index + 1}
                              </div>
                              <div className="text-sm text-gray-700 leading-relaxed">{suggestion}</div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Score Breakdown */}
                  <Card className="card-enhanced">
                    <CardHeader>
                      <CardTitle>Score Breakdown</CardTitle>
                      <CardDescription>Understanding how your score is calculated</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="space-y-2">
                          <div className="font-medium">Tailoring Match</div>
                          <div className="text-gray-600">Up to 30 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">Skills Match</div>
                          <div className="text-gray-600">Up to 20 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">Action Verbs</div>
                          <div className="text-gray-600">Up to 10 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">ATS Safety</div>
                          <div className="text-gray-600">Up to 10 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">Grammar</div>
                          <div className="text-gray-600">Up to 10 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">Structure</div>
                          <div className="text-gray-600">Up to 10 points</div>
                        </div>
                        <div className="space-y-2">
                          <div className="font-medium">Bonus Points</div>
                          <div className="text-gray-600">Up to 10 points</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}

              {!analysisResult && !error && (
                <Card className="card-enhanced border-dashed">
                  <CardContent className="flex items-center justify-center h-64">
                    <div className="text-center space-y-2">
                      <div className="text-gray-400 text-lg">Analysis results will appear here</div>
                      <div className="text-gray-500 text-sm">Upload your resume and click analyze to get started</div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

{/* Contact Section */}
<footer className="relative z-10 mt-16 bg-white/80 backdrop-blur-md border-t border-gray-200 py-10 px-4">
  <div className="max-w-4xl mx-auto text-center space-y-4">
    <h2 className="text-2xl font-semibold text-gray-800">Connect with Me</h2>
    <p className="text-gray-600">Feel free to reach out or follow me on social media!</p>
    <div className="flex justify-center gap-6 mt-4">
      <a
        href="https://www.linkedin.com/in/ram-naren-b6141a218"
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-700 hover:text-blue-900 text-lg font-medium underline"
      >
        LinkedIn
      </a>
      <a
        href="https://www.instagram.com/thisisramnaren/"
        target="_blank"
        rel="noopener noreferrer"
        className="text-pink-600 hover:text-pink-800 text-lg font-medium underline"
      >
        Instagram
      </a>
    </div>
  </div>
</footer>
