import { useState, useEffect, useCallback } from 'react'
import './App.css'

const API_BASE = ''

function App() {
  // Model status
  const [modelLoaded, setModelLoaded] = useState(false)
  const [status, setStatus] = useState({ status: 'idle', progress: 0, message: '' })

  // Form state
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('low quality, blurry, distorted, deformed, ugly, bad anatomy')
  const [aspectRatio, setAspectRatio] = useState('portrait')
  const [numFrames, setNumFrames] = useState(81)
  const [numInferenceSteps, setNumInferenceSteps] = useState(30)
  const [guidanceScale, setGuidanceScale] = useState(5.0)
  const [seed, setSeed] = useState('')
  const [fps, setFps] = useState(16)

  // Video state
  const [videos, setVideos] = useState([])
  const [selectedVideo, setSelectedVideo] = useState(null)

  // Fetch status periodically
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`)
      const data = await res.json()
      setStatus(data)

      // Check if generation completed
      if (data.status === 'completed') {
        fetchVideos()
      }
    } catch (err) {
      console.error('Failed to fetch status:', err)
    }
  }, [])

  // Fetch videos list
  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/videos`)
      const data = await res.json()
      setVideos(data.videos)
      if (data.videos.length > 0 && !selectedVideo) {
        setSelectedVideo(data.videos[0].url)
      }
    } catch (err) {
      console.error('Failed to fetch videos:', err)
    }
  }

  // Check health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/health`)
        const data = await res.json()
        setModelLoaded(data.model_loaded)
      } catch (err) {
        console.error('Failed to check health:', err)
      }
    }
    checkHealth()
    fetchVideos()
  }, [])

  // Poll status when generating or loading
  useEffect(() => {
    if (status.status === 'generating' || status.status === 'loading') {
      const interval = setInterval(fetchStatus, 1000)
      return () => clearInterval(interval)
    }
  }, [status.status, fetchStatus])

  // Load model
  const handleLoadModel = async () => {
    try {
      await fetch(`${API_BASE}/api/load-model`, { method: 'POST' })
      setStatus({ status: 'loading', progress: 0, message: 'Loading model...' })

      // Poll until loaded
      const checkLoaded = setInterval(async () => {
        const res = await fetch(`${API_BASE}/api/health`)
        const data = await res.json()
        if (data.model_loaded) {
          setModelLoaded(true)
          clearInterval(checkLoaded)
        }
      }, 2000)
    } catch (err) {
      console.error('Failed to load model:', err)
    }
  }

  // Unload model
  const handleUnloadModel = async () => {
    try {
      await fetch(`${API_BASE}/api/unload-model`, { method: 'POST' })
      setModelLoaded(false)
    } catch (err) {
      console.error('Failed to unload model:', err)
    }
  }

  // Generate video
  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt')
      return
    }

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          negative_prompt: negativePrompt,
          aspect_ratio: aspectRatio,
          num_frames: numFrames,
          num_inference_steps: numInferenceSteps,
          guidance_scale: guidanceScale,
          seed: seed ? parseInt(seed) : null,
          fps
        })
      })

      if (!res.ok) {
        const error = await res.json()
        alert(error.detail || 'Generation failed')
        return
      }

      setStatus({ status: 'generating', progress: 0, message: 'Starting generation...' })
    } catch (err) {
      console.error('Failed to generate:', err)
      alert('Failed to start generation')
    }
  }

  // Random seed
  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 4294967295).toString())
  }

  // Get status indicator class
  const getStatusClass = () => {
    if (status.status === 'loading' || status.status === 'generating') return 'loading'
    if (status.status === 'error') return 'error'
    if (modelLoaded) return 'loaded'
    return ''
  }

  // Get status text
  const getStatusText = () => {
    if (status.status === 'loading') return 'Connecting...'
    if (status.status === 'generating') return 'Generating...'
    if (status.status === 'error') return 'Error'
    if (modelLoaded) return 'ComfyUI Ready'
    return 'ComfyUI Not Running'
  }

  const isGenerating = status.status === 'generating'
  const isLoading = status.status === 'loading'

  return (
    <div className="app">
      <header className="header">
        <h1>WAN 2.2 Short Video Generator</h1>
        <div className="model-status">
          <div className="status-indicator">
            <div className={`status-dot ${getStatusClass()}`}></div>
            <span>{getStatusText()}</span>
          </div>
          {!modelLoaded ? (
            <button
              className="btn btn-primary"
              onClick={handleLoadModel}
              disabled={isLoading}
            >
              Connect
            </button>
          ) : (
            <button
              className="btn btn-secondary"
              onClick={handleLoadModel}
              disabled={isGenerating || isLoading}
            >
              Refresh
            </button>
          )}
        </div>
      </header>

      <main className="main-content">
        <div className="controls-panel">
          {/* Prompt Section */}
          <div className="panel">
            <h3 className="panel-title">Prompt</h3>
            <div className="form-group">
              <label>Prompt</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the video you want to generate..."
                disabled={isGenerating}
              />
            </div>
            <div className="form-group">
              <label>Negative Prompt</label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="What to avoid in the video..."
                disabled={isGenerating}
              />
            </div>
          </div>

          {/* Aspect Ratio Section */}
          <div className="panel">
            <h3 className="panel-title">Aspect Ratio (480P)</h3>
            <div className="ratio-selector">
              <div
                className={`ratio-option ${aspectRatio === 'portrait' ? 'selected' : ''}`}
                onClick={() => !isGenerating && setAspectRatio('portrait')}
              >
                <div className="ratio-preview portrait"></div>
                <span className="ratio-label">Portrait (480x832)</span>
              </div>
              <div
                className={`ratio-option ${aspectRatio === 'landscape' ? 'selected' : ''}`}
                onClick={() => !isGenerating && setAspectRatio('landscape')}
              >
                <div className="ratio-preview landscape"></div>
                <span className="ratio-label">Landscape (832x480)</span>
              </div>
            </div>
          </div>

          {/* Generation Settings */}
          <div className="panel">
            <h3 className="panel-title">Generation Settings</h3>

            <div className="form-group">
              <div className="slider-group">
                <div className="slider-header">
                  <label>Frames</label>
                  <span className="slider-value">{numFrames}</span>
                </div>
                <input
                  type="range"
                  min="17"
                  max="129"
                  step="4"
                  value={numFrames}
                  onChange={(e) => setNumFrames(parseInt(e.target.value))}
                  disabled={isGenerating}
                />
                <span className="frames-hint">~{(numFrames / fps).toFixed(1)}s at {fps}fps</span>
              </div>
            </div>

            <div className="form-group">
              <div className="slider-group">
                <div className="slider-header">
                  <label>Inference Steps</label>
                  <span className="slider-value">{numInferenceSteps}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={numInferenceSteps}
                  onChange={(e) => setNumInferenceSteps(parseInt(e.target.value))}
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div className="form-group">
              <div className="slider-group">
                <div className="slider-header">
                  <label>Guidance Scale</label>
                  <span className="slider-value">{guidanceScale.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="0.5"
                  value={guidanceScale}
                  onChange={(e) => setGuidanceScale(parseFloat(e.target.value))}
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div className="form-group">
              <div className="slider-group">
                <div className="slider-header">
                  <label>FPS</label>
                  <span className="slider-value">{fps}</span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="30"
                  value={fps}
                  onChange={(e) => setFps(parseInt(e.target.value))}
                  disabled={isGenerating}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Seed (optional)</label>
              <div className="seed-input">
                <input
                  type="text"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  placeholder="Random"
                  disabled={isGenerating}
                />
                <button
                  className="btn btn-secondary btn-icon"
                  onClick={handleRandomSeed}
                  disabled={isGenerating}
                  title="Random seed"
                >
                  🎲
                </button>
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <div className="generate-section">
            <button
              className="btn btn-primary btn-full"
              onClick={handleGenerate}
              disabled={!modelLoaded || isGenerating || !prompt.trim()}
            >
              {isGenerating ? 'Generating...' : 'Generate Video'}
            </button>

            {(isGenerating || isLoading) && (
              <>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${status.progress * 100}%` }}
                  ></div>
                </div>
                <p className="status-message">{status.message}</p>
              </>
            )}
          </div>
        </div>

        <div className="preview-panel">
          <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <h3 className="panel-title">Preview</h3>
            <div className="video-preview">
              {selectedVideo ? (
                <video
                  key={selectedVideo}
                  src={selectedVideo}
                  controls
                  autoPlay
                  loop
                />
              ) : (
                <div className="video-placeholder">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/>
                  </svg>
                  <p>No video selected</p>
                </div>
              )}
            </div>
          </div>

          {videos.length > 0 && (
            <div className="panel">
              <h3 className="panel-title">Generated Videos</h3>
              <div className="video-list">
                {videos.map((video) => (
                  <div
                    key={video.url}
                    className={`video-thumbnail ${selectedVideo === video.url ? 'selected' : ''}`}
                    onClick={() => setSelectedVideo(video.url)}
                  >
                    <video src={video.url} muted />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
