'use client';

import { useState, useEffect, useRef } from 'react';

// Types
interface JobState {
  status: 'idle' | 'generating' | 'complete' | 'error';
  progress: number;
  message: string;
  slideCount: number;
  slideTitles: string[];
  downloadUrl: string | null;
  error: string | null;
  jobId: string | null;
  streamId: string | null;
}

interface StreamEvent {
  type: string;
  timestamp: string;
  data: any;
}

interface ActiveStream {
  stream_id: string;
  job_id: string;
  topic: string;
  username: string;
  status: string;
  created_at: string;
}

const themes = [
  { value: 'professional', label: 'Professional', color: 'bg-slate-600' },
  { value: 'academic', label: 'Academic', color: 'bg-blue-600' },
  { value: 'creative', label: 'Creative', color: 'bg-purple-600' },
  { value: 'minimal', label: 'Minimal', color: 'bg-gray-600' }
];

const progressSteps = [
  { key: 'job_started', label: 'Starting', progress: 5 },
  { key: 'llm_processing', label: 'AI Processing', progress: 20 },
  { key: 'slides_generated', label: 'Slides Generated', progress: 40 },
  { key: 'layout_processing', label: 'Layout Processing', progress: 45 },
  { key: 'slides_processing', label: 'Processing Slides', progress: 50 },
  { key: 'building_pptx', label: 'Building PPTX', progress: 60 },
  { key: 'slide_progress', label: 'Adding Content', progress: 70 },
  { key: 'finalizing', label: 'Finalizing', progress: 75 },
  { key: 'pptx_built', label: 'PPTX Built', progress: 80 },
  { key: 'uploading', label: 'Uploading', progress: 85 },
  { key: 'upload_complete', label: 'Upload Complete', progress: 95 },
  { key: 'job_complete', label: 'Complete', progress: 100 }
];

export default function PPTGenerator() {
  // State management
  const [formData, setFormData] = useState({
    topic: '',
    username: 'suman',
    num_slides: 8,
    include_images: true,
    include_diagrams: true,
    theme: 'professional',
    use_template: false,
    sync: false
  });

  const [jobState, setJobState] = useState<JobState>({
    status: 'idle',
    progress: 0,
    message: '',
    slideCount: 0,
    slideTitles: [],
    downloadUrl: null,
    error: null,
    jobId: null,
    streamId: null
  });

  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [activeStreams, setActiveStreams] = useState<ActiveStream[]>([]);
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const consoleRef = useRef<HTMLDivElement>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Check server health on component mount
  useEffect(() => {
    checkServerHealth();
    fetchActiveStreams();
    const interval = setInterval(fetchActiveStreams, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll console to bottom
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [streamEvents]);

  const checkServerHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }
    } catch (error) {
      setServerStatus('offline');
    }
  };

  const fetchActiveStreams = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/streams/active`);
      if (response.ok) {
        const data = await response.json();
        setActiveStreams(data.streams || []);
      }
    } catch (error) {
      console.error('Failed to fetch active streams:', error);
    }
  };

  const addStreamEvent = (type: string, data: any) => {
    const event: StreamEvent = {
      type,
      timestamp: new Date().toISOString(),
      data
    };
    
    setStreamEvents(prev => [...prev, event]);
    
    // Update progress based on event type
    const step = progressSteps.find(s => s.key === type);
    if (step) {
      setJobState(prev => ({
        ...prev,
        progress: step.progress,
        message: step.label
      }));
    }
  };

  const setupEventSource = (streamId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE_URL}/stream/${streamId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('EventSource connection opened');
      addStreamEvent('connected', { message: 'Connected to real-time stream' });
    };

    eventSource.onmessage = (event) => {
      console.log('EventSource message:', event);
      try {
        const data = JSON.parse(event.data);
        addStreamEvent('message', data);
      } catch (error) {
        console.error('Failed to parse EventSource message:', error);
        addStreamEvent('message', { message: event.data });
      }
    };

    eventSource.onerror = (event) => {
      console.error('EventSource error:', event);
      addStreamEvent('connection_error', { message: 'Stream connection lost' });
      
      // Try to reconnect after a delay
      setTimeout(() => {
        if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
          console.log('Attempting to reconnect...');
          setupEventSource(streamId);
        }
      }, 2000);
    };

    eventSource.addEventListener('job_started', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Job started' };
        addStreamEvent('job_started', data);
        setJobState(prev => ({ ...prev, status: 'generating' }));
      } catch (error) {
        addStreamEvent('job_started', { message: 'Job started' });
        setJobState(prev => ({ ...prev, status: 'generating' }));
      }
    });

    eventSource.addEventListener('llm_processing', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Processing with AI' };
        addStreamEvent('llm_processing', data);
      } catch (error) {
        addStreamEvent('llm_processing', { message: 'Processing with AI' });
      }
    });

    eventSource.addEventListener('slides_generated', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Slides generated' };
        addStreamEvent('slides_generated', data);
        setJobState(prev => ({
          ...prev,
          slideCount: data.slide_count || 0,
          slideTitles: data.slide_titles || []
        }));
      } catch (error) {
        addStreamEvent('slides_generated', { message: 'Slides generated' });
      }
    });

    eventSource.addEventListener('layout_processing', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Processing layouts' };
        addStreamEvent('layout_processing', data);
      } catch (error) {
        addStreamEvent('layout_processing', { message: 'Processing layouts' });
      }
    });

    eventSource.addEventListener('slides_processing', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Processing slides' };
        addStreamEvent('slides_processing', data);
      } catch (error) {
        addStreamEvent('slides_processing', { message: 'Processing slides' });
      }
    });

    eventSource.addEventListener('building_pptx', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Building PPTX' };
        addStreamEvent('building_pptx', data);
      } catch (error) {
        addStreamEvent('building_pptx', { message: 'Building PPTX' });
      }
    });

    eventSource.addEventListener('slide_progress', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Adding slide content' };
        addStreamEvent('slide_progress', data);
      } catch (error) {
        addStreamEvent('slide_progress', { message: 'Adding slide content' });
      }
    });

    eventSource.addEventListener('finalizing', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Finalizing presentation' };
        addStreamEvent('finalizing', data);
      } catch (error) {
        addStreamEvent('finalizing', { message: 'Finalizing presentation' });
      }
    });

    eventSource.addEventListener('pptx_built', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'PPTX built' };
        addStreamEvent('pptx_built', data);
      } catch (error) {
        addStreamEvent('pptx_built', { message: 'PPTX built' });
      }
    });

    eventSource.addEventListener('uploading', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Uploading' };
        addStreamEvent('uploading', data);
      } catch (error) {
        addStreamEvent('uploading', { message: 'Uploading' });
      }
    });

    eventSource.addEventListener('upload_complete', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Upload complete' };
        addStreamEvent('upload_complete', data);
      } catch (error) {
        addStreamEvent('upload_complete', { message: 'Upload complete' });
      }
    });

    eventSource.addEventListener('job_complete', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'Job complete' };
        addStreamEvent('job_complete', data);
        setJobState(prev => ({
          ...prev,
          status: 'complete',
          progress: 100,
          downloadUrl: data.download_url || null,
          message: 'Generation completed successfully!'
        }));
        eventSource.close();
      } catch (error) {
        addStreamEvent('job_complete', { message: 'Job complete' });
        setJobState(prev => ({
          ...prev,
          status: 'complete',
          progress: 100,
          message: 'Generation completed successfully!'
        }));
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (event: MessageEvent) => {
      try {
        const data = event.data ? JSON.parse(event.data) : { message: 'An error occurred' };
        addStreamEvent('error', data);
        setJobState(prev => ({
          ...prev,
          status: 'error',
          error: data.error || data.message || 'Unknown error occurred'
        }));
        eventSource.close();
      } catch (error) {
        addStreamEvent('error', { message: 'An error occurred' });
        setJobState(prev => ({
          ...prev,
          status: 'error',
          error: 'Unknown error occurred'
        }));
        eventSource.close();
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.topic.trim()) {
      setJobState(prev => ({
        ...prev,
        status: 'error',
        error: 'Please enter a topic'
      }));
      return;
    }

    // Reset state
    setJobState({
      status: 'generating',
      progress: 0,
      message: 'Initializing...',
      slideCount: 0,
      slideTitles: [],
      downloadUrl: null,
      error: null,
      jobId: null,
      streamId: null
    });
    setStreamEvents([]);

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Generation failed');
      }

      const data = await response.json();
      
      setJobState(prev => ({
        ...prev,
        jobId: data.job_id,
        streamId: data.stream_id
      }));

      // Set up real-time streaming
      if (data.stream_id && typeof EventSource !== 'undefined') {
        setupEventSource(data.stream_id);
      } else {
        // Fallback to polling
        pollJobStatus(data.job_id);
      }

      addStreamEvent('job_created', {
        message: `Job created: ${data.job_id}`,
        job_id: data.job_id,
        stream_id: data.stream_id
      });

    } catch (error: any) {
      setJobState(prev => ({
        ...prev,
        status: 'error',
        error: error.message
      }));
      addStreamEvent('request_error', { message: error.message });
    }
  };

  const pollJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
      const data = await response.json();

      if (data.status === 'done') {
        setJobState(prev => ({
          ...prev,
          status: 'complete',
          progress: 100,
          downloadUrl: data.online_url,
          message: 'Generation completed!'
        }));
        addStreamEvent('job_complete', {
          message: 'Job completed via polling',
          download_url: data.online_url
        });
      } else if (data.status === 'error') {
        setJobState(prev => ({
          ...prev,
          status: 'error',
          error: data.error
        }));
        addStreamEvent('error', { message: data.error });
      } else {
        addStreamEvent('status_update', { 
          message: `Job status: ${data.status}`,
          status: data.status 
        });
        setTimeout(() => pollJobStatus(jobId), 2000);
      }
    } catch (error: any) {
      addStreamEvent('polling_error', { message: error.message });
    }
  };

  const resetForm = () => {
    setJobState({
      status: 'idle',
      progress: 0,
      message: '',
      slideCount: 0,
      slideTitles: [],
      downloadUrl: null,
      error: null,
      jobId: null,
      streamId: null
    });
    setStreamEvents([]);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  const getEventIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      connected: '🔗',
      job_started: '🚀',
      llm_processing: '🤖',
      slides_generated: '📄',
      layout_processing: '🎨',
      slides_processing: '⚙️',
      building_pptx: '🔨',
      slide_progress: '📝',
      finalizing: '✨',
      pptx_built: '📋',
      uploading: '☁️',
      upload_complete: '✅',
      job_complete: '🎉',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || '📡';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                PPT Generator Pro
              </h1>
              <p className="text-gray-600 mt-1">
                AI-powered presentation creator with real-time streaming
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
                serverStatus === 'online' 
                  ? 'bg-green-100 text-green-800' 
                  : serverStatus === 'offline'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  serverStatus === 'online' 
                    ? 'bg-green-500' 
                    : serverStatus === 'offline'
                    ? 'bg-red-500'
                    : 'bg-yellow-500'
                }`}></div>
                <span>Server {serverStatus}</span>
              </div>
              <div className="text-sm text-gray-500">
                Active Streams: {activeStreams.length}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* Left Column - Form */}
          <div className="xl:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <span className="bg-blue-100 text-blue-600 p-2 rounded-lg mr-3">
                  ⚙️
                </span>
                Configuration
              </h2>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Topic Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Topic *
                  </label>
                  <input
                    type="text"
                    value={formData.topic}
                    onChange={(e) => setFormData(prev => ({ ...prev, topic: e.target.value }))}
                    placeholder="e.g., Machine Learning Fundamentals"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                    disabled={jobState.status === 'generating'}
                  />
                </div>

                {/* Username */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <input
                  title='enter your username'
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                    disabled={jobState.status === 'generating'}
                  />
                </div>

                {/* Number of Slides */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Slides: {formData.num_slides}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={formData.num_slides}
                    onChange={(e) => setFormData(prev => ({ ...prev, num_slides: parseInt(e.target.value) }))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    disabled={jobState.status === 'generating'}
                    title={`Number of slides: ${formData.num_slides}`}
                    aria-label="Number of slides"
                    placeholder="Select number of slides"
                  />
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>1</span>
                    <span>20</span>
                  </div>
                </div>

                {/* Theme Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Theme
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {themes.map((theme) => (
                      <button
                        key={theme.value}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, theme: theme.value }))}
                        className={`flex items-center space-x-3 p-3 rounded-lg border-2 transition-all ${
                          formData.theme === theme.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        disabled={jobState.status === 'generating'}
                      >
                        <div className={`w-4 h-4 rounded ${theme.color}`}></div>
                        <span className="text-sm font-medium">{theme.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Options */}
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Options
                  </label>
                  
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.include_images}
                        onChange={(e) => setFormData(prev => ({ ...prev, include_images: e.target.checked }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        disabled={jobState.status === 'generating'}
                      />
                      <span className="ml-3 text-sm text-gray-700">Include Images</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.include_diagrams}
                        onChange={(e) => setFormData(prev => ({ ...prev, include_diagrams: e.target.checked }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        disabled={jobState.status === 'generating'}
                      />
                      <span className="ml-3 text-sm text-gray-700">Include Diagrams</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.use_template}
                        onChange={(e) => setFormData(prev => ({ ...prev, use_template: e.target.checked }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        disabled={jobState.status === 'generating'}
                      />
                      <span className="ml-3 text-sm text-gray-700">Use Template</span>
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3 pt-4">
                  <button
                    type="submit"
                    disabled={jobState.status === 'generating' || !formData.topic.trim()}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
                  >
                    {jobState.status === 'generating' ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        🚀 Generate PPT
                      </>
                    )}
                  </button>

                  {jobState.status !== 'idle' && (
                    <button
                      type="button"
                      onClick={resetForm}
                      className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                    >
                      Reset
                    </button>
                  )}
                </div>
              </form>
            </div>

            {/* Active Streams */}
            {activeStreams.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6 mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="bg-green-100 text-green-600 p-2 rounded-lg mr-3">
                    📡
                  </span>
                  Active Streams ({activeStreams.length})
                </h3>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {activeStreams.map((stream) => (
                    <div key={stream.stream_id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {stream.topic}
                          </p>
                          <p className="text-xs text-gray-500">
                            {stream.username} • {stream.status}
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          stream.status === 'running' 
                            ? 'bg-blue-100 text-blue-800'
                            : stream.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {stream.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Progress and Console */}
          <div className="xl:col-span-2 space-y-6">
            
            {/* Progress Section */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <span className="bg-green-100 text-green-600 p-2 rounded-lg mr-3">
                  📊
                </span>
                Progress Monitor
              </h2>

              {jobState.status === 'idle' ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎯</div>
                  <h3 className="text-xl font-medium text-gray-900 mb-2">
                    Ready to Generate
                  </h3>
                  <p className="text-gray-600">
                    Fill in the form and click "Generate PPT" to start creating your presentation
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        {jobState.message}
                      </span>
                      <span className="text-sm text-gray-500">
                        {jobState.progress}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all duration-500 ${
                          jobState.status === 'error' 
                            ? 'bg-red-500' 
                            : jobState.status === 'complete'
                            ? 'bg-green-500'
                            : 'bg-blue-500'
                        }`}
                        style={{ width: `${Math.min(jobState.progress, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Status Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Job Info */}
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">Job Info</h4>
                      <div className="space-y-1 text-sm text-blue-800">
                        <p>Topic: {formData.topic}</p>
                        <p>Slides: {formData.num_slides}</p>
                        <p>Theme: {formData.theme}</p>
                      </div>
                    </div>

                    {/* Generated Content */}
                    <div className="bg-green-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-green-900 mb-2">Generated</h4>
                      <div className="space-y-1 text-sm text-green-800">
                        <p>Slides Created: {jobState.slideCount}</p>
                        <p>Status: {jobState.status}</p>
                        {jobState.jobId && (
                          <p className="truncate">ID: {jobState.jobId.substring(0, 8)}...</p>
                        )}
                      </div>
                    </div>

                    {/* Download */}
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-purple-900 mb-2">Download</h4>
                      {jobState.downloadUrl ? (
                        <a
                          href={jobState.downloadUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-1 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                        >
                          📥 Download PPT
                        </a>
                      ) : (
                        <p className="text-sm text-purple-800">
                          {jobState.status === 'complete' ? 'Processing...' : 'Not ready'}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Slide Titles */}
                  {jobState.slideTitles.length > 0 && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">
                        Generated Slides ({jobState.slideTitles.length})
                      </h4>
                      <div className="grid gap-2">
                        {jobState.slideTitles.map((title, index) => (
                          <div key={index} className="flex items-center space-x-3 p-2 bg-white rounded border">
                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                              {index + 1}
                            </span>
                            <span className="text-sm text-gray-900 truncate">{title}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Error Display */}
                  {jobState.error && (
                    <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                      <div className="flex items-center">
                        <span className="text-red-500 mr-2">❌</span>
                        <h4 className="text-sm font-medium text-red-900">Error</h4>
                      </div>
                      <p className="text-sm text-red-800 mt-2">{jobState.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Real-time Console */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <span className="bg-gray-100 text-gray-600 p-2 rounded-lg mr-3">
                    💻
                  </span>
                  Real-time Console
                </h2>
                <button
                  onClick={() => setStreamEvents([])}
                  className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Clear
                </button>
              </div>

              <div
                ref={consoleRef}
                className="console-terminal p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto"
              >
                {streamEvents.length === 0 ? (
                  <div className="text-gray-500 text-center py-8">
                    <div className="text-2xl mb-2">📡</div>
                    <p>Waiting for events...</p>
                    <p className="text-xs mt-1">Real-time updates will appear here</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {streamEvents.map((event, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <span className="text-gray-500 text-xs mt-1 w-20 flex-shrink-0">
                          {formatTimestamp(event.timestamp)}
                        </span>
                        <span className="text-lg">{getEventIcon(event.type)}</span>
                        <div className="flex-1">
                          <span className="text-blue-400 font-medium">
                            [{event.type}]
                          </span>
                          <span className="ml-2">
                            {event.data.message || JSON.stringify(event.data)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <p className="text-gray-600 text-sm">
              PPT Generator Pro - AI-powered presentation creator
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>API: {API_BASE_URL}</span>
              <span>•</span>
              <span>Version 1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
