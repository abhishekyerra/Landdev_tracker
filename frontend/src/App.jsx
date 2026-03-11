import { useState, useEffect, useRef } from 'react';
import './App.css';

function getDayName(day, index) {
  // If day object has a name field (from weather API), use it directly
  if (day && day.name) {
    return day.name;
  }
  
  // Fallback to index-based calculation
  const today = new Date();
  const targetDate = new Date(today);
  targetDate.setDate(today.getDate() + index);
  
  if (index === 0) return 'Today';
  if (index === 1) return 'Tomorrow';
  return targetDate.toLocaleDateString('en-US', { weekday: 'long' });
}
function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectDetails, setProjectDetails] = useState(null);
  const [weather, setWeather] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [aiRecommendations, setAiRecommendations] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const [projectFiles, setProjectFiles] = useState([]);
  const [showFilesPanel, setShowFilesPanel] = useState(false);
  const [showBudgetPanel, setShowBudgetPanel] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [analyzingFiles, setAnalyzingFiles] = useState(false);
  const [rebuildingTasks, setRebuildingTasks] = useState(false);
  const [aiInstruction, setAiInstruction] = useState('');
  const [documentAnalyses, setDocumentAnalyses] = useState([]);
  const [taskChangeLog, setTaskChangeLog] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [fileNameFilter, setFileNameFilter] = useState('');
  const fileInputRef = useRef(null);

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    checkBackendConnection();
    if (token) {
      fetchUserData();
      loadProjects();
    }
  }, [token]);

  const checkBackendConnection = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/health`);
      setBackendConnected(response.ok);
    } catch (err) {
      setBackendConnected(false);
    }
  };

  const fetchUserData = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (err) {
      console.error('Error fetching user:', err);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('Error loading projects:', err);
    }
  };

  const login = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password })
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
      } else {
        setError('Incorrect email or password');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setProjects([]);
    setSelectedProject(null);
    localStorage.removeItem('token');
  };

  const selectProject = async (project) => {
  setSelectedProject(project);
  setTaskChangeLog([]);
  setShowBudgetPanel(false);
  await loadProjectDetails(project.project_id);
  await loadWeather();
  await loadAIRecommendations(project.project_id);
  await loadProjectFiles(project.project_id);
  await loadDocumentAnalyses(project.project_id);
};

  const loadProjectDetails = async (projectId) => {
    try {
      const response = await fetch(`${apiUrl}/api/projects/${projectId}/phases`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjectDetails({ phases: data });
      }
    } catch (err) {
      console.error('Error loading project details:', err);
    }
  };

  const loadWeather = async () => {
    setLoadingWeather(true);
    try {
      const response = await fetch(`${apiUrl}/api/weather/columbia-tn`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setWeather(data);
      }
    } catch (err) {
      console.error('Error loading weather:', err);
    }
    setLoadingWeather(false);
  };

  const loadAIRecommendations = async (projectId) => {
    setLoadingAI(true);
    try {
      const response = await fetch(`${apiUrl}/api/ai/recommendations/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAiRecommendations(data);
      }
    } catch (err) {
      console.error('Error loading AI recommendations:', err);
    }
    setLoadingAI(false);
  };

const refreshProject = () => {
  if (selectedProject) {
    loadProjectDetails(selectedProject.project_id);
    loadAIRecommendations(selectedProject.project_id);
    loadProjectFiles(selectedProject.project_id);
    loadDocumentAnalyses(selectedProject.project_id);
  }
};

// ADD THESE THREE FUNCTIONS AFTER refreshProject() function:

const loadProjectFiles = async (projectId) => {
  if (!projectId) return;
  
  try {
    const response = await fetch(`${apiUrl}/api/projects/${projectId}/files`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const files = await response.json();
      setProjectFiles(files);
      setSelectedDocumentIds([]);
    }
  } catch (err) {
    console.error('Error loading files:', err);
  }
};

const loadDocumentAnalyses = async (projectId) => {
  if (!projectId) return;
  try {
    const response = await fetch(`${apiUrl}/api/projects/${projectId}/ai/tasks-from-docs`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      const runs = await response.json();
      setDocumentAnalyses(runs);
    }
  } catch (err) {
    console.error('Error loading document analyses:', err);
  }
};

const handleFileUpload = async (event) => {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;

  setUploadingFiles(true);
  
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  try {
    const response = await fetch(
      `${apiUrl}/api/projects/${selectedProject.project_id}/upload-files?auto_generate_tasks=true`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      }
    );

    if (response.ok) {
      const result = await response.json();
      const failures = result.analysis_failures || [];
      setTaskChangeLog((result.generated_tasks || []).slice(0, 200));
      const warningText = failures.length > 0
        ? `\n⚠️ AI analysis skipped/failed for ${failures.length} file(s). Select files and run Analyze Selected again.`
        : '';
      alert(`✅ Success!\n\n📁 ${result.files_uploaded} files uploaded\n🤖 ${result.tasks_generated} tasks generated by AI${warningText}\n\nRefreshing project...`);
      
      await loadProjectFiles(selectedProject.project_id);
      await loadProjectDetails(selectedProject.project_id);
      await loadAIRecommendations(selectedProject.project_id);
      await loadDocumentAnalyses(selectedProject.project_id);
    } else {
      const error = await response.json();
      alert(`Upload failed (${response.status}): ${error.detail || 'Unknown backend error'}`);
    }
  } catch (err) {
    console.error('Upload error:', err);
    alert(`Error uploading files: ${err.message || 'Network/unknown error'}`);
  } finally {
    setUploadingFiles(false);
    event.target.value = '';
  }
};

const analyzeSelectedFiles = async () => {
  if (!selectedProject || selectedDocumentIds.length === 0) return;
  setAnalyzingFiles(true);
  try {
    const response = await fetch(
      `${apiUrl}/api/projects/${selectedProject.project_id}/documents/analyze-selected`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: selectedDocumentIds,
          ai_instruction: aiInstruction.trim() || null
        })
      }
    );
    if (response.ok) {
      const result = await response.json();
      setTaskChangeLog((result.generated_tasks || []).slice(0, 200));
      alert(`AI analyzed ${result.documents_analyzed} selected file(s) and generated ${result.tasks_generated} task(s).`);
      await loadProjectDetails(selectedProject.project_id);
      await loadAIRecommendations(selectedProject.project_id);
      await loadProjectFiles(selectedProject.project_id);
      await loadDocumentAnalyses(selectedProject.project_id);
    } else {
      const error = await response.json();
      alert(error.detail || 'Failed to analyze selected files');
    }
  } catch (err) {
    alert('Error analyzing selected files');
  } finally {
    setAnalyzingFiles(false);
  }
};

const rebuildTasksFromFiles = async () => {
  if (!selectedProject) return;
  const ok = confirm('This will delete ALL existing tasks in this project and regenerate tasks from uploaded files. Continue?');
  if (!ok) return;

  setRebuildingTasks(true);
  try {
    const response = await fetch(
      `${apiUrl}/api/projects/${selectedProject.project_id}/tasks/rebuild-from-files`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ai_instruction: aiInstruction.trim() || null,
          clear_analysis_history: true
        })
      }
    );
    if (response.ok) {
      const result = await response.json();
      setTaskChangeLog((result.generated_tasks || []).slice(0, 300));
      alert(`Rebuild complete.\nDeleted: ${result.tasks_deleted} task(s)\nAnalyzed: ${result.documents_analyzed} file(s)\nGenerated: ${result.tasks_generated} task(s)`);
      await loadProjectDetails(selectedProject.project_id);
      await loadAIRecommendations(selectedProject.project_id);
      await loadProjectFiles(selectedProject.project_id);
      await loadDocumentAnalyses(selectedProject.project_id);
    } else {
      const error = await response.json();
      alert(error.detail || 'Failed to rebuild tasks from files');
    }
  } catch (err) {
    alert('Error rebuilding tasks from files');
  } finally {
    setRebuildingTasks(false);
  }
};

const toggleSelectDocument = (documentId) => {
  setSelectedDocumentIds((prev) =>
    prev.includes(documentId) ? prev.filter((id) => id !== documentId) : [...prev, documentId]
  );
};

const openFile = async (documentId) => {
  if (!selectedProject) return;
  try {
    const response = await fetch(
      `${apiUrl}/api/projects/${selectedProject.project_id}/files/${documentId}/open`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    if (!response.ok) {
      const error = await response.json();
      alert(error.detail || 'Unable to open file');
      return;
    }
    const data = await response.json();
    if (data.open_url) {
      window.open(data.open_url, '_blank', 'noopener,noreferrer');
    } else {
      const dl = await fetch(`${apiUrl}${data.download_url}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!dl.ok) {
        alert('Unable to stream file from server.');
        return;
      }
      const blob = await dl.blob();
      const blobUrl = URL.createObjectURL(blob);
      window.open(blobUrl, '_blank', 'noopener,noreferrer');
      setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
    }
  } catch (err) {
    alert('Error opening file');
  }
};

const filteredFiles = projectFiles.filter((file) => {
  const nameOk = !fileNameFilter.trim() || file.filename.toLowerCase().includes(fileNameFilter.toLowerCase());
  return nameOk;
});

const deleteFile = async (documentId) => {
  if (!confirm('Are you sure you want to delete this file?')) return;

  try {
    const response = await fetch(
      `${apiUrl}/api/projects/${selectedProject.project_id}/files/${documentId}`,
      {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    if (response.ok) {
      alert('File deleted successfully');
      loadProjectFiles(selectedProject.project_id);
    }
  } catch (err) {
    alert('Error deleting file');
  }
};


  if (!token) {
    return <LoginPage 
      email={email}
      setEmail={setEmail}
      password={password}
      setPassword={setPassword}
      onLogin={login}
      error={error}
      backendConnected={backendConnected}
    />;
  }

  if (selectedProject) {
return <ProjectDetail
  project={selectedProject}
  details={projectDetails}
  weather={weather}
  loadingWeather={loadingWeather}
  aiRecommendations={aiRecommendations}
  loadingAI={loadingAI}
  apiUrl={apiUrl}
  token={token}
  onBack={() => setSelectedProject(null)}
  onRefresh={refreshProject}
  onRefreshWeather={loadWeather}
  onRefreshAI={() => loadAIRecommendations(selectedProject.project_id)}
  projectFiles={projectFiles}
  showFilesPanel={showFilesPanel}
  setShowFilesPanel={setShowFilesPanel}
  showBudgetPanel={showBudgetPanel}
  setShowBudgetPanel={setShowBudgetPanel}
  uploadingFiles={uploadingFiles}
  analyzingFiles={analyzingFiles}
  rebuildingTasks={rebuildingTasks}
  aiInstruction={aiInstruction}
  setAiInstruction={setAiInstruction}
  analyzeSelectedFiles={analyzeSelectedFiles}
  rebuildTasksFromFiles={rebuildTasksFromFiles}
  documentAnalyses={documentAnalyses}
  taskChangeLog={taskChangeLog}
  selectedDocumentIds={selectedDocumentIds}
  fileNameFilter={fileNameFilter}
  setFileNameFilter={setFileNameFilter}
  filteredFiles={filteredFiles}
  toggleSelectDocument={toggleSelectDocument}
  openFile={openFile}
  handleFileUpload={handleFileUpload}
  deleteFile={deleteFile}
  fileInputRef={fileInputRef}
  getDayName={getDayName}
/>;
  }

  return <Dashboard
    projects={projects}
    onSelectProject={selectProject}
    onLogout={logout}
    onRefresh={loadProjects}
    apiUrl={apiUrl}
  />;
}

// Login Page Component
function ABHLogo({ size = 36, textSize = 14, variant = 'light' }) {
  const isDark = variant === 'dark';
  const textPrimary = isDark ? '#f8fafc' : '#0f172a';
  const textSecondary = isDark ? '#cbd5f5' : '#475569';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
        <defs>
          <linearGradient id="abhShield" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={isDark ? '#1e293b' : '#0f172a'} />
            <stop offset="100%" stopColor={isDark ? '#38bdf8' : '#0f766e'} />
          </linearGradient>
          <linearGradient id="abhAccent" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>
        </defs>
        <path d="M32 4 L54 12 V30 C54 44 44 54 32 60 C20 54 10 44 10 30 V12 Z" fill="url(#abhShield)"/>
        <path d="M20 36 L24 24 L28 36 L32 24 L36 36 L40 24 L44 36" stroke={isDark ? '#e2e8f0' : '#e2e8f0'} strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M14 40 L30 40 L30 44 L14 44 Z" fill="url(#abhAccent)"/>
        <circle cx="18" cy="46" r="3" fill="url(#abhAccent)"/>
        <circle cx="28" cy="46" r="3" fill="url(#abhAccent)"/>
        <path d="M34 40 L46 28 L50 30 L38 42 Z" fill="url(#abhAccent)"/>
        <path d="M46 28 L54 26" stroke="#fef3c7" strokeWidth="2" strokeLinecap="round"/>
        <text x="32" y="22" textAnchor="middle" fontSize="12" fill={isDark ? '#e2e8f0' : '#e2e8f0'} fontFamily="Helvetica, Arial, sans-serif">ABH</text>
      </svg>
      <div style={{ lineHeight: 1 }}>
        <div style={{ fontWeight: 800, fontSize: textSize, color: textPrimary }}>ABH</div>
        <div style={{ fontSize: textSize - 4, color: textSecondary }}>Adroit Business Holdings</div>
      </div>
    </div>
  );
}

function LoginPage({ email, setEmail, password, setPassword, onLogin, error, backendConnected }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 12% 18%, #dbeafe 0%, #bfdbfe 18%, transparent 45%), radial-gradient(circle at 88% 10%, #e0f2fe 0%, #bae6fd 20%, transparent 48%), linear-gradient(140deg, #f0f9ff 0%, #e0f2fe 45%, #eef6ff 100%)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: '20px', right: '24px' }}>
        <ABHLogo size={40} textSize={14} variant="dark" />
      </div>
      <div style={{ background: 'white', padding: '40px', borderRadius: '14px', border: '1px solid #e2e8f0', boxShadow: '0 20px 40px rgba(15, 23, 42, 0.12)', maxWidth: '420px', width: '100%' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '10px' }}>Adroit Business Holdings</h1>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>Sign in to your account</p>
        
        {backendConnected && (
          <div style={{ background: '#d4edda', color: '#155724', padding: '10px', borderRadius: '4px', marginBottom: '20px', fontSize: '14px', textAlign: 'center' }}>
            ✓ Backend connected
          </div>
        )}
        
        {error && (
          <div style={{ background: '#f8d7da', color: '#721c24', padding: '10px', borderRadius: '4px', marginBottom: '20px' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={onLogin}>
          <input
            type="email"
            placeholder="admin@landdev.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '12px', marginBottom: '15px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '16px' }}
            required
          />
          <input
            type="password"
            placeholder="••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '12px', marginBottom: '20px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '16px' }}
            required
          />
          <button type="submit" style={{ width: '100%', padding: '12px', background: '#5b63f4', color: 'white', border: 'none', borderRadius: '4px', fontSize: '16px', cursor: 'pointer' }}>
            Sign in
          </button>
        </form>
        
        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px', color: '#666' }}>
          Default: admin@landdev.com / Password123!
        </p>
      </div>
    </div>
  );
}

// Dashboard Component
function Dashboard({ projects, onSelectProject, onLogout, onRefresh, apiUrl }) {
  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 8% 14%, #dbeafe 0%, #bfdbfe 22%, transparent 48%), radial-gradient(circle at 92% 8%, #e0f2fe 0%, #bae6fd 22%, transparent 50%), linear-gradient(155deg, #f0f9ff 0%, #e0f2fe 55%, #eef6ff 100%)' }}>
      <div style={{ background: 'linear-gradient(90deg, #0f172a, #1f2937, #052e2b)', color: 'white', borderBottom: '1px solid #1f2937', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '24px', color: 'white' }}>Adroit Business Holdings</h1>
          <button style={{ padding: '8px 16px', background: 'rgba(255,255,255,0.15)', color: 'white', border: '1px solid rgba(255,255,255,0.3)', borderRadius: '6px', cursor: 'pointer' }}>
            Dashboard
          </button>
        </div>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <ABHLogo size={32} textSize={12} variant="dark" />
          <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer" style={{ color: '#a5b4fc', textDecoration: 'none' }}>
            API Docs →
          </a>
          <button onClick={onLogout} style={{ padding: '8px 20px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </div>

      <div style={{ padding: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h2 style={{ margin: 0 }}>Your Projects</h2>
          <button onClick={onRefresh} style={{ padding: '10px 22px', background: 'linear-gradient(90deg, #06b6d4, #3b82f6)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
            Refresh
          </button>
        </div>

        {projects.length === 0 ? (
          <div style={{ background: 'linear-gradient(180deg, #ffffff, #f8fafc)', padding: '60px', textAlign: 'center', borderRadius: '14px', color: '#64748b', border: '1px solid #dbeafe' }}>
            No projects found
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {projects.map(project => (
              <div key={project.project_id} onClick={() => onSelectProject(project)} style={{ background: 'linear-gradient(165deg, #ffffff, #f1f5f9)', padding: '24px', borderRadius: '14px', cursor: 'pointer', border: '1px solid #bfdbfe', transition: 'box-shadow 0.2s' }} 
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 10px 24px rgba(37, 99, 235, 0.18)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                  <div>
                    <h3 style={{ margin: '0 0 8px 0' }}>{project.project_name}</h3>
                    <span style={{ fontSize: '14px', color: '#666' }}>{project.project_code}</span>
                  </div>
                  <span style={{ background: project.status === 'in_progress' ? '#dbeafe' : '#f1f5f9', color: project.status === 'in_progress' ? '#1d4ed8' : '#475569', padding: '4px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: '700' }}>
                    {project.status?.replace('_', ' ')}
                  </span>
                </div>
                <p style={{ margin: '12px 0', color: '#666', fontSize: '14px' }}>{project.description}</p>
                {project.location_city && (
                  <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: '#999' }}>
                    📍 {project.location_city}, {project.location_state}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
// Project Detail Component - FULLY FIXED
// =================================================================
// COMPLETE CORRECTED ProjectDetail COMPONENT
// Replace your entire ProjectDetail function (starting around line 437)
// =================================================================

function ProjectDetail({ 
  project, details, weather, loadingWeather, 
  aiRecommendations, loadingAI, apiUrl, token, 
  onBack, onRefresh, onRefreshWeather, onRefreshAI,
  projectFiles, showFilesPanel, setShowFilesPanel, showBudgetPanel, setShowBudgetPanel,
  uploadingFiles, analyzingFiles, rebuildingTasks, aiInstruction, setAiInstruction, analyzeSelectedFiles, rebuildTasksFromFiles, documentAnalyses, taskChangeLog,
  selectedDocumentIds, toggleSelectDocument, openFile,
  fileNameFilter, setFileNameFilter, filteredFiles,
  handleFileUpload, deleteFile,
  fileInputRef, getDayName
}) {
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [phaseTasks, setPhaseTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [dailyUpdate, setDailyUpdate] = useState({
    notes: '',
    weather_conditions: '',
    crew_size: 1,
    hours_worked: 8,
    equipment_used: '',
    materials_received: '',
    issues_encountered: '',
    safety_incidents: ''
  });
  const [showDailyUpdate, setShowDailyUpdate] = useState(false);
  const [submittingUpdate, setSubmittingUpdate] = useState(false);
  const [updateResult, setUpdateResult] = useState(null);
  const [budgetSummary, setBudgetSummary] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [phaseBudgetDashboard, setPhaseBudgetDashboard] = useState([]);
  const [loadingBudgetData, setLoadingBudgetData] = useState(false);
  const [invoiceReviewing, setInvoiceReviewing] = useState(false);
  const [invoiceReviewResult, setInvoiceReviewResult] = useState(null);
  const [budgetForm, setBudgetForm] = useState({
    budget_name: '',
    budgeted_amount: '',
    phase_id: '',
    contingency_percentage: '10',
    notes: ''
  });
  const [expenseForm, setExpenseForm] = useState({
    description: '',
    amount: '',
    expense_date: new Date().toISOString().slice(0, 10),
    budget_id: '',
    phase_id: '',
    invoice_number: '',
    payment_status: 'pending',
    notes: ''
  });
  const [taskForm, setTaskForm] = useState({
    task_name: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    due_date: '',
    estimated_hours: '',
    completion_percentage: ''
  });
  const [bulkTaskText, setBulkTaskText] = useState('');
  const [savingTask, setSavingTask] = useState(false);
  const [savingBulkTasks, setSavingBulkTasks] = useState(false);
  const [updatingExpenseId, setUpdatingExpenseId] = useState(null);
  const [taskStatusFilter, setTaskStatusFilter] = useState('all');

  const loadPhaseTasks = async (phaseId) => {
    setSelectedPhase(phaseId);
    setLoadingTasks(true);
    try {
      const response = await fetch(`${apiUrl}/api/phases/${phaseId}/tasks`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPhaseTasks(data);
      }
    } catch (err) {
      console.error('Error loading tasks:', err);
    }
    setLoadingTasks(false);
  };


  const updateTaskStatus = async (taskId, newStatus) => {
    try {
      await fetch(`${apiUrl}/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (selectedPhase) {
        loadPhaseTasks(selectedPhase);
      }
      onRefresh();
    } catch (err) {
      console.error('Error updating task:', err);
    }
  };

  const updateTaskCompletion = async (taskId, value) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
      alert('Completion must be between 0 and 100');
      return;
    }
    try {
      await fetch(`${apiUrl}/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ completion_percentage: Math.round(parsed) })
      });
      if (selectedPhase) {
        loadPhaseTasks(selectedPhase);
      }
      onRefresh();
    } catch (err) {
      console.error('Error updating task completion:', err);
    }
  };

  const createManualTask = async () => {
    if (!selectedPhase) {
      alert('Select a phase first');
      return;
    }
    if (!taskForm.task_name.trim()) {
      alert('Task name is required');
      return;
    }
    setSavingTask(true);
    try {
      const response = await fetch(`${apiUrl}/api/phases/${selectedPhase}/tasks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_name: taskForm.task_name.trim(),
          description: taskForm.description || null,
          priority: taskForm.priority,
          status: taskForm.status,
          due_date: taskForm.due_date || null,
          estimated_hours: taskForm.estimated_hours ? Number(taskForm.estimated_hours) : null,
          completion_percentage: taskForm.completion_percentage !== '' ? Number(taskForm.completion_percentage) : null
        })
      });
      const result = await response.json();
      if (!response.ok) {
        alert(result.detail || 'Failed to create task');
        return;
      }
      setTaskForm({ task_name: '', description: '', priority: 'medium', status: 'todo', due_date: '', estimated_hours: '', completion_percentage: '' });
      await loadPhaseTasks(selectedPhase);
      onRefresh();
    } catch (err) {
      alert('Error creating task');
    } finally {
      setSavingTask(false);
    }
  };

  const bulkCreateTasks = async () => {
    if (!selectedPhase) {
      alert('Select a phase first');
      return;
    }
    const lines = bulkTaskText.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) {
      alert('Paste at least one task line');
      return;
    }
    const tasks = lines.map((line) => {
      const parts = line.split('|').map((p) => p.trim());
      return {
        task_name: parts[0] || '',
        priority: parts[1] || 'medium',
        status: parts[2] || 'todo',
        estimated_hours: parts[3] ? Number(parts[3]) : null,
        due_date: parts[4] || null,
        completion_percentage: parts[5] ? Number(parts[5]) : null,
        description: parts[6] || null
      };
    }).filter((t) => t.task_name);

    if (tasks.length === 0) {
      alert('No valid task names found in bulk input.');
      return;
    }

    setSavingBulkTasks(true);
    try {
      const response = await fetch(`${apiUrl}/api/phases/${selectedPhase}/tasks/bulk`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tasks })
      });
      const result = await response.json();
      if (!response.ok) {
        alert(result.detail || 'Bulk task create failed');
        return;
      }
      setBulkTaskText('');
      await loadPhaseTasks(selectedPhase);
      onRefresh();
      alert(`Created ${result.created_count || tasks.length} task(s).`);
    } catch (err) {
      alert('Error creating bulk tasks');
    } finally {
      setSavingBulkTasks(false);
    }
  };

  const editTask = async (task) => {
    const newName = prompt('Task name', task.task_name || '');
    if (newName === null) return;
    const newDescription = prompt('Description', task.description || '');
    if (newDescription === null) return;
    const newPriority = prompt('Priority (critical/high/medium/low)', task.priority || 'medium');
    if (newPriority === null) return;
    const newDueDate = prompt('Due date (YYYY-MM-DD or blank)', task.due_date || '');
    if (newDueDate === null) return;
    const newHours = prompt('Estimated hours (number or blank)', task.estimated_hours || '');
    if (newHours === null) return;

    try {
      const response = await fetch(`${apiUrl}/api/tasks/${task.task_id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_name: newName.trim() || task.task_name,
          description: newDescription || null,
          priority: (newPriority || task.priority || 'medium').toLowerCase(),
          due_date: newDueDate || null,
          estimated_hours: newHours ? Number(newHours) : null
        })
      });
      const result = await response.json();
      if (!response.ok) {
        alert(result.detail || 'Failed to update task');
        return;
      }
      await loadPhaseTasks(selectedPhase);
      onRefresh();
    } catch (err) {
      alert('Error updating task');
    }
  };

  const deleteTask = async (taskId) => {
    const ok = confirm('Delete this task?');
    if (!ok) return;
    try {
      let response = await fetch(`${apiUrl}/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.status === 405) {
        response = await fetch(`${apiUrl}/api/tasks/${taskId}/delete`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      }
      const contentType = response.headers.get('content-type') || '';
      const result = contentType.includes('application/json')
        ? await response.json()
        : { detail: await response.text() };
      if (!response.ok) {
        alert(result.detail || 'Failed to delete task');
        return;
      }
      await loadPhaseTasks(selectedPhase);
      onRefresh();
    } catch (err) {
      alert('Error deleting task');
    }
  };

  const updateExpensePaymentStatus = async (expenseId, uiStatus) => {
    setUpdatingExpenseId(expenseId);
    const mapped = uiStatus === 'to_be_paid' ? 'pending' : uiStatus;
    try {
      const response = await fetch(`${apiUrl}/api/expenses/${expenseId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          payment_status: mapped,
          payment_date: mapped === 'paid' ? new Date().toISOString().slice(0, 10) : null
        })
      });
      const result = await response.json();
      if (!response.ok) {
        alert(result.detail || 'Failed to update invoice status');
        return;
      }
      await loadBudgetData();
    } catch (err) {
      alert('Error updating invoice status');
    } finally {
      setUpdatingExpenseId(null);
    }
  };

  const submitDailyUpdate = async () => {
    if (!dailyUpdate.notes.trim()) {
      alert('Please enter your daily update notes');
      return;
    }
    
    setSubmittingUpdate(true);
    setUpdateResult(null);
    
    try {
      const response = await fetch(`${apiUrl}/api/projects/${project.project_id}/daily-update`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dailyUpdate)
      });
      
      if (response.ok) {
        const result = await response.json();
        const analysis = result.analysis || {};
        setUpdateResult({ 
          success: true, 
          message: `${result.message || 'Daily update submitted!'}${result.tasks_generated ? ` Generated ${result.tasks_generated} task(s).` : ''}${result.invoices_marked_paid ? ` Marked ${result.invoices_marked_paid} invoice(s) as paid.` : ''}`,
          analysis: analysis,
          updatedProgress: result.updated_progress || null
        });
        setDailyUpdate({
          notes: '',
          weather_conditions: '',
          crew_size: 1,
          hours_worked: 8,
          equipment_used: '',
          materials_received: '',
          issues_encountered: '',
          safety_incidents: ''
        });
        // Refresh phases and AI after update
        onRefresh();
        onRefreshAI();
      } else {
        const errorBody = await response.json().catch(() => ({}));
        setUpdateResult({ success: false, message: errorBody.detail || 'Error submitting update' });
      }
    } catch (err) {
      setUpdateResult({ success: false, message: 'Error submitting update' });
    }
    
    setSubmittingUpdate(false);
  };

  const loadBudgetData = async () => {
    setLoadingBudgetData(true);
    try {
      const [summaryResp, budgetsResp, expensesResp, phaseDashResp] = await Promise.all([
        fetch(`${apiUrl}/api/projects/${project.project_id}/budget-summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiUrl}/api/projects/${project.project_id}/budgets`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiUrl}/api/projects/${project.project_id}/expenses`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiUrl}/api/projects/${project.project_id}/phase-budget-dashboard`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
      ]);

      let budgetsData = [];
      let expensesData = [];
      if (budgetsResp.ok) budgetsData = await budgetsResp.json();
      if (expensesResp.ok) expensesData = await expensesResp.json();

      setBudgets(budgetsData);
      setExpenses(expensesData);
      if (phaseDashResp.ok) {
        const phaseDash = await phaseDashResp.json();
        setPhaseBudgetDashboard(phaseDash.phases || []);
      } else {
        setPhaseBudgetDashboard([]);
      }

      if (summaryResp.ok) {
        setBudgetSummary(await summaryResp.json());
      } else {
        const totalBudgeted = budgetsData.reduce((sum, b) => sum + Number(b.budgeted_amount || 0), 0);
        const totalSpent = expensesData.reduce((sum, e) => sum + Number(e.amount || 0), 0);
        setBudgetSummary({
          total_budgeted: totalBudgeted,
          total_spent: totalSpent,
          remaining_budget: totalBudgeted - totalSpent,
          budget_utilization_percentage: totalBudgeted > 0 ? (totalSpent / totalBudgeted) * 100 : 0
        });
      }
    } catch (err) {
      console.error('Error loading budget data:', err);
    } finally {
      setLoadingBudgetData(false);
    }
  };

  const saveBudget = async () => {
    if (!budgetForm.budget_name || !budgetForm.budgeted_amount) {
      alert('Budget name and amount are required');
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/api/projects/${project.project_id}/budgets`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          budget_name: budgetForm.budget_name,
          budgeted_amount: Number(budgetForm.budgeted_amount),
          phase_id: budgetForm.phase_id || null,
          contingency_percentage: Number(budgetForm.contingency_percentage || 10),
          notes: budgetForm.notes || null
        })
      });
      if (!response.ok) {
        const error = await response.json();
        alert(error.detail || 'Failed to save budget');
        return;
      }
      setBudgetForm({ budget_name: '', budgeted_amount: '', phase_id: '', contingency_percentage: '10', notes: '' });
      await loadBudgetData();
      alert('Budget added');
    } catch (err) {
      alert('Error saving budget');
    }
  };

  const saveExpense = async () => {
    if (!expenseForm.description || !expenseForm.amount || !expenseForm.expense_date) {
      alert('Description, amount, and date are required');
      return;
    }
    try {
      const response = await fetch(`${apiUrl}/api/projects/${project.project_id}/expenses`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          description: expenseForm.description,
          amount: Number(expenseForm.amount),
          expense_date: expenseForm.expense_date,
          budget_id: expenseForm.budget_id || null,
          phase_id: expenseForm.phase_id || null,
          invoice_number: expenseForm.invoice_number || null,
          payment_status: expenseForm.payment_status || 'pending',
          notes: expenseForm.notes || null
        })
      });
      if (!response.ok) {
        const error = await response.json();
        alert(error.detail || 'Failed to save expense');
        return;
      }
      setExpenseForm({
        description: '',
        amount: '',
        expense_date: new Date().toISOString().slice(0, 10),
        budget_id: '',
        phase_id: '',
        invoice_number: '',
        payment_status: 'pending',
        notes: ''
      });
      await loadBudgetData();
      alert('Expense recorded');
    } catch (err) {
      alert('Error saving expense');
    }
  };

  const reviewSelectedInvoices = async () => {
    if (selectedDocumentIds.length === 0) {
      alert('Select project files first, then run invoice review.');
      return;
    }
    setInvoiceReviewing(true);
    setInvoiceReviewResult(null);
    try {
      const response = await fetch(`${apiUrl}/api/projects/${project.project_id}/invoices/review-selected`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: selectedDocumentIds,
          auto_record_expense: true
        })
      });
      const result = await response.json();
      if (!response.ok) {
        alert(result.detail || 'Invoice review failed');
        return;
      }
      setInvoiceReviewResult(result);
      await loadBudgetData();
    } catch (err) {
      alert('Error reviewing invoices');
    } finally {
      setInvoiceReviewing(false);
    }
  };

  useEffect(() => {
    if (showBudgetPanel) {
      loadBudgetData();
    }
  }, [showBudgetPanel, project.project_id]);

  const phaseCompletionValues = details?.phases?.map((p) => Number(p.completion_percentage || 0)) || [];
  const avgWorkCompletion = phaseCompletionValues.length > 0
    ? (phaseCompletionValues.reduce((a, b) => a + b, 0) / phaseCompletionValues.length)
    : 0;
  const budgetUsedPct = Number(budgetSummary?.budget_utilization_percentage || 0);
  const filteredPhaseTasks = phaseTasks.filter((task) => taskStatusFilter === 'all' || task.status === taskStatusFilter);

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 10% 16%, #dbeafe 0%, #bfdbfe 22%, transparent 48%), radial-gradient(circle at 90% 12%, #e0f2fe 0%, #bae6fd 24%, transparent 50%), linear-gradient(150deg, #f0f9ff 0%, #e0f2fe 48%, #eef6ff 100%)' }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(90deg, #111827, #1f2937, #064e3b)', borderBottom: '1px solid #0f172a', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <button onClick={onBack} style={{ padding: '10px 20px', background: '#e8e8e8', border: '2px solid #999', borderRadius: '6px', cursor: 'pointer', color: '#000', fontWeight: '600', fontSize: '15px' }}>
            ← Back
          </button>
          <h1 style={{ margin: 0, fontSize: '24px', color: '#ffffff' }}>{project.project_name}</h1>
          <span style={{ fontSize: '14px', color: '#cbd5e1' }}>{project.project_code}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ABHLogo size={32} textSize={12} variant="dark" />
          <button onClick={onRefresh} style={{ padding: '10px 22px', background: 'linear-gradient(90deg, #4f46e5, #7c3aed)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', boxShadow: '0 8px 18px rgba(79, 70, 229, 0.3)' }}>
            Refresh All
          </button>
        </div>
      </div>

      {/* Main Content - Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '20px', padding: '20px 40px' }}>
        
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => setShowDailyUpdate(!showDailyUpdate)}
              style={{
                padding: '12px 24px',
                background: showDailyUpdate ? '#4caf50' : '#fff',
                color: showDailyUpdate ? '#fff' : '#4caf50',
                border: '2px solid #4caf50',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '15px'
              }}
            >
              📝 Submit Daily Update
            </button>
            
            <button
              onClick={() => setShowFilesPanel(!showFilesPanel)}
              style={{
                padding: '12px 24px',
                background: showFilesPanel ? '#5b63f4' : '#fff',
                color: showFilesPanel ? '#fff' : '#5b63f4',
                border: '2px solid #5b63f4',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '15px'
              }}
            >
              📁 Project Files {projectFiles.length > 0 && `(${projectFiles.length})`}
            </button>

            <button
              onClick={() => setShowBudgetPanel(!showBudgetPanel)}
              style={{
                padding: '12px 24px',
                background: showBudgetPanel ? '#0f766e' : '#fff',
                color: showBudgetPanel ? '#fff' : '#0f766e',
                border: '2px solid #0f766e',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '15px'
              }}
            >
              💰 Budget & Invoices
            </button>
          </div>

          {/* Daily Update Panel */}
          {showDailyUpdate && (
            <div style={{ background: 'linear-gradient(180deg, #ffffff, #f0fdf4)', padding: '24px', borderRadius: '12px', border: '1px solid #86efac', boxShadow: '0 8px 20px rgba(34, 197, 94, 0.12)' }}>
              <h3 style={{ margin: '0 0 16px 0', color: '#4caf50' }}>📝 Daily Update - {new Date().toLocaleDateString()}</h3>
              
              {updateResult && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ 
                    padding: '12px', 
                    marginBottom: '12px', 
                    borderRadius: '4px',
                    background: updateResult.success ? '#d4edda' : '#f8d7da',
                    color: updateResult.success ? '#155724' : '#721c24',
                    fontWeight: '600'
                  }}>
                    {updateResult.success ? '✅' : '❌'} {updateResult.message}
                  </div>
                  
                  {updateResult.success && updateResult.analysis && (
                    <div style={{ background: '#f8f9fa', borderRadius: '8px', padding: '16px', border: '1px solid #e0e0e0' }}>
                      <h4 style={{ margin: '0 0 12px 0', color: '#1a1a2e' }}>🤖 AI Analysis</h4>
                      
                      {updateResult.analysis.progress_assessment && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: '700', fontSize: '13px', color: '#555', marginBottom: '4px' }}>PROGRESS ASSESSMENT</div>
                          <div style={{ fontSize: '14px' }}>{updateResult.analysis.progress_assessment}</div>
                        </div>
                      )}

                      {updateResult.analysis.next_actions?.length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: '700', fontSize: '13px', color: '#555', marginBottom: '4px' }}>TOMORROW'S ACTIONS</div>
                          {updateResult.analysis.next_actions.map((action, i) => (
                            <div key={i} style={{ fontSize: '14px', padding: '4px 0', borderLeft: '3px solid #4caf50', paddingLeft: '8px', marginBottom: '4px' }}>
                              {action}
                            </div>
                          ))}
                        </div>
                      )}

                      {updateResult.analysis.risks?.length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: '700', fontSize: '13px', color: '#c62828', marginBottom: '4px' }}>⚠️ RISKS</div>
                          {updateResult.analysis.risks.map((risk, i) => (
                            <div key={i} style={{ fontSize: '14px', padding: '4px 8px', background: '#fff3e0', borderLeft: '3px solid #f57c00', marginBottom: '4px', borderRadius: '2px' }}>
                              {risk}
                            </div>
                          ))}
                        </div>
                      )}

                      {updateResult.analysis.strategic_guidance && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: '700', fontSize: '13px', color: '#555', marginBottom: '4px' }}>💡 STRATEGIC GUIDANCE</div>
                          <div style={{ fontSize: '14px', background: '#f3e5f5', padding: '10px', borderRadius: '4px', borderLeft: '3px solid #7b1fa2' }}>
                            {updateResult.analysis.strategic_guidance}
                          </div>
                        </div>
                      )}

                      {updateResult.updatedProgress && updateResult.updatedProgress.phase && (
                        <div style={{ background: '#e3f2fd', padding: '10px', borderRadius: '4px', fontSize: '14px' }}>
                          📊 Phase updated: <strong>{updateResult.updatedProgress.phase}</strong> — {updateResult.updatedProgress.completion}% complete
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {/* Helper text showing what AI will do */}
              <div style={{ background: '#e8f5e9', border: '1px solid #a5d6a7', borderRadius: '6px', padding: '10px 14px', marginBottom: '12px', fontSize: '13px', color: '#2e7d32' }}>
                🤖 <strong>AI will automatically:</strong> Analyze your notes · Update task statuses · Flag risks in red · Adjust phase progress
              </div>

              <textarea
                placeholder="What did you accomplish today? Any issues or blockers? (e.g. 'Completed grading on lots 74-80. Slope stabilization has an issue with soil erosion on north side.')"
                value={dailyUpdate.notes}
                onChange={(e) => setDailyUpdate({ ...dailyUpdate, notes: e.target.value })}
                style={{ width: '100%', minHeight: '140px', padding: '12px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px', resize: 'vertical', marginBottom: '12px' }}
              />

              {/* Submitting spinner */}
              {submittingUpdate && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', padding: '12px', background: '#fff3e0', borderRadius: '6px', border: '1px solid #ffcc80' }}>
                  <div style={{ width: '20px', height: '20px', border: '3px solid #ff9800', borderTop: '3px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                  <span style={{ fontSize: '14px', color: '#e65100', fontWeight: '600' }}>🤖 AI is analyzing your update and updating tasks...</span>
                </div>
              )}

              <button 
                onClick={submitDailyUpdate}
                disabled={submittingUpdate}
                style={{ 
                  padding: '12px 28px', 
                  background: submittingUpdate ? '#ccc' : '#4caf50', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '6px', 
                  cursor: submittingUpdate ? 'not-allowed' : 'pointer', 
                  fontWeight: '700',
                  fontSize: '15px',
                  width: '100%'
                }}>
                {submittingUpdate ? '⏳ AI Analyzing...' : '🚀 Submit Daily Update & Run AI Analysis'}
              </button>

              <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
            </div>
          )}

          {/* FILES PANEL */}
          {showFilesPanel && (
            <div style={{
              background: 'linear-gradient(180deg, #ffffff, #f8fafc)',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 10px 22px rgba(15, 23, 42, 0.08)',
              border: '1px solid #dbeafe'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>📁 Documents & AI Workspace</h3>
                  <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                    Files are stored in cloud storage and tracked here. Run AI analysis to generate tasks.
                  </p>
                </div>
                
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={rebuildTasksFromFiles}
                    disabled={rebuildingTasks || uploadingFiles || analyzingFiles || projectFiles.length === 0}
                    style={{
                      padding: '10px 14px',
                      background: rebuildingTasks ? '#9ca3af' : '#14532d',
                      color: '#dcfce7',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: rebuildingTasks ? 'not-allowed' : 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    {rebuildingTasks ? '⏳ Rebuilding...' : '♻️ Reset & Rebuild Tasks'}
                  </button>

                  <button
                    onClick={analyzeSelectedFiles}
                    disabled={analyzingFiles || selectedDocumentIds.length === 0}
                    style={{
                      padding: '10px 16px',
                      background: analyzingFiles ? '#9ca3af' : '#111827',
                      color: '#d1fae5',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: analyzingFiles ? 'not-allowed' : 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    {analyzingFiles ? '⏳ Working...' : `🎯 Analyze Selected (${selectedDocumentIds.length})`}
                  </button>

                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingFiles}
                    style={{
                      padding: '10px 20px',
                      background: uploadingFiles ? '#ccc' : '#5b63f4',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: uploadingFiles ? 'not-allowed' : 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    {uploadingFiles ? '⏳ Uploading...' : '📤 Upload Files'}
                  </button>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.xlsx,.xls,.docx,.doc,.txt,.csv,.png,.jpg,.jpeg,.dwg,.dxf"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
              </div>

              <div style={{ marginBottom: '16px', background: 'linear-gradient(120deg, #eff6ff, #ecfeff)', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '14px' }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#1d4ed8', marginBottom: '8px' }}>
                  AI Instruction (optional)
                </div>
                <textarea
                  placeholder="Example: Prioritize permitting and utility tasks first; ignore landscaping until Phase 3."
                  value={aiInstruction}
                  onChange={(e) => setAiInstruction(e.target.value)}
                  style={{ width: '100%', minHeight: '70px', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '10px', fontSize: '13px' }}
                />
              </div>
              <div style={{ marginBottom: '16px', background: 'linear-gradient(120deg, #f0fdf4, #f8fafc)', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#14532d', marginBottom: '8px' }}>
                  File Selection
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="text"
                    placeholder="Filter by filename (example: permit, utility, grading)"
                    value={fileNameFilter}
                    onChange={(e) => setFileNameFilter(e.target.value)}
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid #a7f3d0' }}
                  />
                  <button
                    onClick={() => setFileNameFilter('')}
                    style={{ padding: '8px 10px', background: '#111827', color: '#d1fae5', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Clear
                  </button>
                </div>
                <div style={{ marginTop: '8px', display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => setSelectedDocumentIds(filteredFiles.map((f) => f.document_id))}
                    style={{ padding: '6px 10px', background: '#ecfeff', color: '#0f766e', border: '1px solid #99f6e4', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
                  >
                    Select Filtered ({filteredFiles.length})
                  </button>
                  <button
                    onClick={() => setSelectedDocumentIds([])}
                    style={{ padding: '6px 10px', background: '#f8fafc', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
                  >
                    Clear Selection
                  </button>
                </div>
              </div>

              {projectFiles.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '60px 20px', background: '#f8f9fa', borderRadius: '8px', border: '2px dashed #ddd' }}>
                  <div style={{ fontSize: '64px', marginBottom: '16px' }}>📂</div>
                  <h4 style={{ margin: '0 0 8px 0', color: '#666' }}>No files uploaded yet</h4>
                  <p style={{ margin: 0, fontSize: '14px', color: '#999' }}>
                    Click "Upload Files" to add project documents
                  </p>
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                      <th style={{ padding: '12px', textAlign: 'center' }}>Use</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Filename</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Type</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>AI</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Uploaded</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>By</th>
                      <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map(file => (
                      <tr key={file.document_id} style={{ borderBottom: '1px solid #e9ecef' }}>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={selectedDocumentIds.includes(file.document_id)}
                            onChange={() => toggleSelectDocument(file.document_id)}
                          />
                        </td>
                        <td style={{ padding: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>
                              {file.filename.endsWith('.pdf') ? '📄' :
                               file.filename.endsWith('.xlsx') || file.filename.endsWith('.xls') ? '📊' :
                               file.filename.endsWith('.docx') || file.filename.endsWith('.doc') ? '📝' :
                               file.filename.match(/\.(jpg|jpeg|png)$/i) ? '🖼️' : '📎'}
                            </span>
                            <span style={{ fontWeight: '500' }}>{file.filename}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px', color: '#666' }}>{file.file_type || 'Unknown'}</td>
                        <td style={{ padding: '12px' }}>
                          <span style={{
                            background: file.ai_status === 'completed' ? '#dcfce7' : file.ai_status === 'failed' ? '#fee2e2' : '#e2e8f0',
                            color: file.ai_status === 'completed' ? '#166534' : file.ai_status === 'failed' ? '#991b1b' : '#334155',
                            padding: '4px 8px',
                            borderRadius: '999px',
                            fontSize: '12px',
                            fontWeight: '600',
                          }}>
                            {file.ai_status?.replace('_', ' ') || 'not analyzed'}
                          </span>
                        </td>
                        <td style={{ padding: '12px', color: '#666' }}>
                          {file.uploaded_at ? new Date(file.uploaded_at).toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', year: 'numeric'
                          }) : 'Unknown'}
                        </td>
                        <td style={{ padding: '12px', color: '#666' }}>{file.uploaded_by || 'Unknown'}</td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px' }}>
                            <button
                              onClick={() => openFile(file.document_id)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                padding: 0,
                                margin: 0,
                                cursor: 'pointer',
                                fontSize: '12px',
                                color: '#0f766e',
                                textDecoration: 'underline',
                                fontWeight: '600'
                              }}
                            >
                              Open
                            </button>
                            <button
                              onClick={() => deleteFile(file.document_id)}
                              title="Delete file"
                              style={{
                                background: 'transparent',
                                border: 'none',
                                padding: 0,
                                margin: 0,
                                cursor: 'pointer',
                                fontSize: '12px',
                                color: '#475569',
                                textDecoration: 'underline',
                                fontWeight: '600'
                              }}
                            >
                              🗑 Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              
              <div style={{ marginTop: '20px', padding: '16px', background: '#e3f2fd', borderRadius: '6px', border: '1px solid #90caf9' }}>
                <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
                  <span style={{ fontSize: '20px' }}>🤖</span>
                  <div>
                    <h4 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>AI-Powered Task Generation</h4>
                    <p style={{ margin: 0, fontSize: '14px', color: '#0d47a1', lineHeight: '1.6' }}>
                      Upload files from Google Drive (local sync folder is easiest), select the files, then run Analyze Selected.<br/>
                      AI will:<br/>
                      • Extracts tasks and assigns them to the correct phase<br/>
                      • Sets priorities based on document content<br/>
                      • Estimates hours and identifies dependencies<br/>
                      • Saves each analysis run for auditing
                    </p>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '20px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '14px' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#14532d' }}>Task Change Log (Created / Updated)</h4>
                {taskChangeLog.length === 0 ? (
                  <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>
                    No task changes in this session yet. Run Analyze Selected to populate this log.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
                    {taskChangeLog.slice(0, 60).map((task, idx) => (
                      <div key={`${task.task_name || 'task'}-${idx}`} style={{ background: 'white', border: '1px solid #dcfce7', borderRadius: '6px', padding: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                          <strong style={{ fontSize: '13px' }}>{task.task_name || 'Untitled task'}</strong>
                          <span style={{ fontSize: '12px', color: task.action === 'updated' ? '#0f766e' : '#1d4ed8' }}>
                            {task.action === 'updated' ? 'updated' : 'created'}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#475569' }}>
                          {task.phase || 'Unassigned phase'} · {task.priority || 'medium'} · {task.budget_estimate ? `$${Number(task.budget_estimate).toLocaleString()}` : 'Budget TBD'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ marginTop: '20px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#0f172a' }}>AI Analysis History</h4>
                {documentAnalyses.length === 0 ? (
                  <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>No analysis runs yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
                    {documentAnalyses.slice(0, 25).map((run) => (
                      <div key={run.analysis_id} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                          <strong style={{ fontSize: '13px' }}>{run.document_name}</strong>
                          <span style={{ fontSize: '12px', color: '#475569' }}>{run.status}</span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          Tasks: {run.task_count} · {run.updated_at ? new Date(run.updated_at).toLocaleString() : 'n/a'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {showBudgetPanel && (
            <div style={{
              background: 'linear-gradient(175deg, #ffffff, #ecfeff)',
              padding: '24px',
              borderRadius: '12px',
              border: '1px solid #99f6e4',
              boxShadow: '0 10px 22px rgba(15, 23, 42, 0.08)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ margin: '0 0 6px 0', color: '#134e4a' }}>💰 Budget & Invoices</h3>
                  <p style={{ margin: 0, fontSize: '13px', color: '#0f766e' }}>
                    Track budget usage, record invoices/expenses, and compare spend against work completion.
                  </p>
                </div>
                <button
                  onClick={loadBudgetData}
                  disabled={loadingBudgetData}
                  style={{ padding: '8px 12px', border: 'none', borderRadius: '6px', background: '#0f766e', color: '#ecfeff', fontWeight: '700', cursor: 'pointer' }}
                >
                  {loadingBudgetData ? 'Loading...' : 'Refresh Budget'}
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '14px' }}>
                <div style={{ background: '#ecfeff', border: '1px solid #a5f3fc', borderRadius: '8px', padding: '10px' }}>
                  <div style={{ fontSize: '12px', color: '#0f766e' }}>Total Budget</div>
                  <div style={{ fontWeight: '700' }}>${Number(budgetSummary?.total_budgeted || 0).toLocaleString()}</div>
                </div>
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '10px' }}>
                  <div style={{ fontSize: '12px', color: '#991b1b' }}>Total Spent</div>
                  <div style={{ fontWeight: '700' }}>${Number(budgetSummary?.total_spent || 0).toLocaleString()}</div>
                </div>
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '10px' }}>
                  <div style={{ fontSize: '12px', color: '#166534' }}>Remaining</div>
                  <div style={{ fontWeight: '700' }}>${Number(budgetSummary?.remaining_budget || 0).toLocaleString()}</div>
                </div>
                <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '10px' }}>
                  <div style={{ fontSize: '12px', color: '#334155' }}>Budget Used</div>
                  <div style={{ fontWeight: '700' }}>{budgetUsedPct.toFixed(1)}%</div>
                </div>
              </div>

              <div style={{ marginBottom: '16px', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '10px' }}>
                <div style={{ fontSize: '13px', color: '#1e293b', marginBottom: '6px' }}>
                  <strong>Budget Used vs Work Completed:</strong> {budgetUsedPct.toFixed(1)}% vs {avgWorkCompletion.toFixed(1)}%
                </div>
                <div style={{ fontSize: '12px', color: '#475569' }}>
                  {budgetUsedPct > (avgWorkCompletion + 10)
                    ? '⚠️ Spend is ahead of progress. Review invoices and scope.'
                    : '✅ Spend and progress are within expected range.'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div style={{ border: '1px solid #bbf7d0', borderRadius: '8px', padding: '10px', background: '#f0fdf4' }}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#166534' }}>Add Budget</h4>
                  <input placeholder="Budget name" value={budgetForm.budget_name} onChange={(e) => setBudgetForm({ ...budgetForm, budget_name: e.target.value })} style={{ width: '100%', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #86efac' }} />
                  <input type="number" placeholder="Amount" value={budgetForm.budgeted_amount} onChange={(e) => setBudgetForm({ ...budgetForm, budgeted_amount: e.target.value })} style={{ width: '100%', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #86efac' }} />
                  <select value={budgetForm.phase_id} onChange={(e) => setBudgetForm({ ...budgetForm, phase_id: e.target.value })} style={{ width: '100%', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #86efac' }}>
                    <option value="">No phase</option>
                    {(details?.phases || []).map((p) => (<option key={p.phase_id} value={p.phase_id}>{p.phase_name}</option>))}
                  </select>
                  <button onClick={saveBudget} style={{ width: '100%', padding: '8px', border: 'none', borderRadius: '6px', background: '#15803d', color: 'white', fontWeight: '700', cursor: 'pointer' }}>Save Budget</button>
                </div>

                <div style={{ border: '1px solid #bfdbfe', borderRadius: '8px', padding: '10px', background: '#eff6ff' }}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#1d4ed8' }}>Add Invoice / Expense</h4>
                  <input placeholder="Description" value={expenseForm.description} onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })} style={{ width: '100%', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #93c5fd' }} />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <input type="number" placeholder="Amount" value={expenseForm.amount} onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })} style={{ padding: '8px', borderRadius: '6px', border: '1px solid #93c5fd' }} />
                    <input type="date" value={expenseForm.expense_date} onChange={(e) => setExpenseForm({ ...expenseForm, expense_date: e.target.value })} style={{ padding: '8px', borderRadius: '6px', border: '1px solid #93c5fd' }} />
                  </div>
                  <input placeholder="Invoice #" value={expenseForm.invoice_number} onChange={(e) => setExpenseForm({ ...expenseForm, invoice_number: e.target.value })} style={{ width: '100%', marginTop: '8px', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #93c5fd' }} />
                  <select value={expenseForm.budget_id} onChange={(e) => setExpenseForm({ ...expenseForm, budget_id: e.target.value })} style={{ width: '100%', marginBottom: '8px', padding: '8px', borderRadius: '6px', border: '1px solid #93c5fd' }}>
                    <option value="">No budget link</option>
                    {budgets.map((b) => (<option key={b.budget_id} value={b.budget_id}>{b.budget_name}</option>))}
                  </select>
                  <button onClick={saveExpense} style={{ width: '100%', padding: '8px', border: 'none', borderRadius: '6px', background: '#1d4ed8', color: 'white', fontWeight: '700', cursor: 'pointer' }}>Save Expense</button>
                </div>
              </div>

              <div style={{ marginBottom: '16px', border: '1px solid #fde68a', borderRadius: '8px', background: '#fffbeb', padding: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '13px', color: '#92400e' }}>
                    AI Invoice Review uses selected files from <strong>Project Files</strong> and can auto-record expenses.
                  </div>
                  <button
                    onClick={reviewSelectedInvoices}
                    disabled={invoiceReviewing}
                    style={{ padding: '8px 10px', border: 'none', borderRadius: '6px', background: '#d97706', color: 'white', fontWeight: '700', cursor: 'pointer' }}
                  >
                    {invoiceReviewing ? 'Reviewing...' : 'Review Selected Invoices'}
                  </button>
                </div>
                {invoiceReviewResult && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#78350f' }}>
                    Reviewed: {invoiceReviewResult.reviewed} invoice file(s)
                    {invoiceReviewResult.invoices_marked_paid ? ` · Auto-marked paid: ${invoiceReviewResult.invoices_marked_paid}` : ''}
                    {Array.isArray(invoiceReviewResult.invoices) && invoiceReviewResult.invoices.length > 0 && (
                      <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {invoiceReviewResult.invoices.slice(0, 8).map((inv, idx) => (
                          <div key={`${inv.document_id || idx}`} style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '6px', padding: '6px' }}>
                            <div style={{ fontWeight: '600' }}>{inv.document_name}</div>
                            <div>Category: {inv.inferred_category || 'General'} · Phase: {inv.inferred_phase_name || 'Not assigned'}</div>
                            <div>Amount: ${Number(inv.invoice_amount || 0).toLocaleString()} · Risk: {inv.overpay_risk}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '16px', background: '#ffffff', border: '1px solid #d1fae5', borderRadius: '8px', padding: '10px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#065f46' }}>Phase-wise Budget vs Progress</h4>
                {phaseBudgetDashboard.length === 0 ? (
                  <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>No phase budget data yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {phaseBudgetDashboard.map((p) => (
                      <div key={p.phase_id} style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '12px' }}>
                          <strong>{p.phase_name}</strong>
                          <span>${Number(p.spent || 0).toLocaleString()} / ${Number(p.budgeted || 0).toLocaleString()}</span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#475569', marginBottom: '4px' }}>
                          Completion: {Number(p.completion_percentage || 0).toFixed(0)}% · Budget Used: {Number(p.budget_utilization_percentage || 0).toFixed(0)}%
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '4px' }}>
                          <div style={{ height: '7px', background: '#e2e8f0', borderRadius: '999px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Number(p.completion_percentage || 0))}%`, height: '100%', background: '#10b981' }} />
                          </div>
                          <div style={{ height: '7px', background: '#e2e8f0', borderRadius: '999px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Number(p.budget_utilization_percentage || 0))}%`, height: '100%', background: '#3b82f6' }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '10px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#0f172a' }}>Invoices & Expenses</h4>
                {expenses.length === 0 ? (
                  <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>No expenses recorded yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '260px', overflowY: 'auto' }}>
                    {expenses.map((e) => (
                      <div key={e.expense_id} style={{ border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px', fontSize: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'center' }}>
                          <strong style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.description}</strong>
                          <span>${Number(e.amount || 0).toLocaleString()}</span>
                        </div>
                        <div style={{ color: '#64748b', margin: '4px 0 6px 0' }}>{e.expense_date} {e.invoice_number ? `· Invoice ${e.invoice_number}` : ''}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <label style={{ color: '#334155' }}>Payment:</label>
                          <select
                            value={e.payment_status === 'pending' ? 'to_be_paid' : e.payment_status}
                            onChange={(evt) => updateExpensePaymentStatus(e.expense_id, evt.target.value)}
                            disabled={updatingExpenseId === e.expense_id}
                            style={{ padding: '4px 8px', border: '1px solid #cbd5e1', borderRadius: '6px' }}
                          >
                            <option value="to_be_paid">To Be Paid</option>
                            <option value="approved">Approved</option>
                            <option value="paid">Paid</option>
                            <option value="rejected">Rejected</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Development Phases */}
          <div style={{ background: 'linear-gradient(170deg, #ffffff, #ecfeff)', padding: '24px', borderRadius: '12px', border: '1px solid #99f6e4' }}>
            <h3 style={{ margin: '0 0 20px 0' }}>Development Phases</h3>
            
            {!details?.phases || details.phases.length === 0 ? (
              <p style={{ color: '#999' }}>No phases found</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {details.phases.map(phase => (
                  <div key={phase.phase_id} style={{ border: '1px solid #cbd5e1', borderRadius: '10px', padding: '16px', cursor: 'pointer', background: '#ffffff' }}
                    onClick={() => loadPhaseTasks(phase.phase_id)}>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h4 style={{ margin: 0 }}>{phase.phase_name}</h4>
                      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <span style={{ background: phase.status === 'in_progress' ? '#e3f2fd' : '#f0f0f0', color: phase.status === 'in_progress' ? '#1976d2' : '#666', padding: '4px 12px', borderRadius: '12px', fontSize: '12px' }}>
                          {phase.status?.replace('_', ' ')}
                        </span>
                        <span style={{ fontWeight: '600', color: '#5b63f4' }}>{phase.completion_percentage || 0}%</span>
                      </div>
                    </div>
                    
                    <div style={{ width: '100%', height: '8px', background: '#f0f0f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ width: `${phase.completion_percentage || 0}%`, height: '100%', background: '#5b63f4' }}></div>
                    </div>
                    
                    <p style={{ margin: '12px 0 0 0', fontSize: '14px', color: '#666' }}>{phase.description}</p>
                    
                    {phase.planned_start_date && (
                      <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#999' }}>
                        {phase.planned_start_date} - {phase.planned_end_date}
                      </p>
                    )}
                    {selectedPhase === phase.phase_id && (
                      <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e0e0e0' }}>
                        <div style={{ background: '#f8fafc', border: '1px solid #dbeafe', borderRadius: '8px', padding: '10px', marginBottom: '12px' }}>
                          <h5 style={{ margin: '0 0 8px 0', color: '#1d4ed8' }}>Manual Task Entry</h5>
                          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                            <input
                              placeholder="Task name"
                              value={taskForm.task_name}
                              onChange={(e) => setTaskForm({ ...taskForm, task_name: e.target.value })}
                              style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}
                            />
                            <select value={taskForm.priority} onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })} style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}>
                              <option value="low">low</option>
                              <option value="medium">medium</option>
                              <option value="high">high</option>
                              <option value="critical">critical</option>
                            </select>
                            <select value={taskForm.status} onChange={(e) => setTaskForm({ ...taskForm, status: e.target.value })} style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}>
                              <option value="todo">todo</option>
                              <option value="in_progress">in_progress</option>
                              <option value="review">review</option>
                              <option value="completed">completed</option>
                            </select>
                            <input
                              type="date"
                              value={taskForm.due_date}
                              onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
                              style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}
                            />
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr 1fr auto', gap: '8px', marginBottom: '8px' }}>
                            <input
                              placeholder="Description (optional)"
                              value={taskForm.description}
                              onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                              style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}
                            />
                            <input
                              type="number"
                              placeholder="Hours"
                              value={taskForm.estimated_hours}
                              onChange={(e) => setTaskForm({ ...taskForm, estimated_hours: e.target.value })}
                              style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}
                            />
                            <input
                              type="number"
                              placeholder="% Complete"
                              value={taskForm.completion_percentage}
                              onChange={(e) => setTaskForm({ ...taskForm, completion_percentage: e.target.value })}
                              style={{ padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px' }}
                            />
                            <button onClick={createManualTask} disabled={savingTask} style={{ padding: '8px 12px', border: 'none', borderRadius: '6px', background: '#1d4ed8', color: 'white', cursor: 'pointer', fontWeight: '700' }}>
                              {savingTask ? 'Saving...' : 'Add Task'}
                            </button>
                          </div>
                          <textarea
                            placeholder={'Bulk paste: task_name|priority|status|hours|YYYY-MM-DD|%complete|description\nExample: Submit grading permit package|high|todo|8|2026-08-10|25|Compile package and submit'}
                            value={bulkTaskText}
                            onChange={(e) => setBulkTaskText(e.target.value)}
                            rows={3}
                            style={{ width: '100%', padding: '8px', border: '1px solid #bfdbfe', borderRadius: '6px', marginBottom: '8px' }}
                          />
                          <button onClick={bulkCreateTasks} disabled={savingBulkTasks} style={{ padding: '8px 12px', border: 'none', borderRadius: '6px', background: '#0f766e', color: 'white', cursor: 'pointer', fontWeight: '700' }}>
                            {savingBulkTasks ? 'Importing...' : 'Import Bulk Tasks'}
                          </button>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <h5 style={{ margin: 0 }}>Tasks</h5>
                          <select
                            value={taskStatusFilter}
                            onChange={(e) => setTaskStatusFilter(e.target.value)}
                            style={{ padding: '6px 8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '12px' }}
                          >
                            <option value="all">All statuses</option>
                            <option value="todo">To Do</option>
                            <option value="in_progress">In Progress</option>
                            <option value="review">Review</option>
                            <option value="completed">Completed</option>
                            <option value="blocked">Blocked</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                        </div>
                        {loadingTasks ? (
                          <p style={{ color: '#999' }}>Loading...</p>
                        ) : filteredPhaseTasks.length === 0 ? (
                          <p style={{ color: '#999' }}>No tasks</p>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {filteredPhaseTasks.map(task => (
                              <div key={task.task_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: '#f9f9f9', borderRadius: '4px' }}>
                                <div>
                                  <div style={{ fontWeight: '500' }}>{task.task_name}</div>
                                  {task.description && <div style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>{task.description}</div>}
                                  <div style={{ fontSize: '12px', color: '#666' }}>
                                    Due: {task.due_date || 'Not set'}
                                    <span style={{ 
                                      marginLeft: '8px',
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      background: task.priority === 'critical' ? '#ffebee' : task.priority === 'high' ? '#fff3e0' : '#f0f0f0',
                                      color: task.priority === 'critical' ? '#c62828' : task.priority === 'high' ? '#f57c00' : '#666'
                                    }}>
                                      {task.priority}
                                    </span>
                                  </div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-end' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input
                                      type="number"
                                      min="0"
                                      max="100"
                                      value={task.completion_percentage ?? (task.status === 'completed' ? 100 : '')}
                                      onChange={(e) => updateTaskCompletion(task.task_id, e.target.value)}
                                      style={{ width: '70px', padding: '5px 6px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px' }}
                                    />
                                    <span style={{ fontSize: '12px', color: '#475569' }}>%</span>
                                  </div>
                                  <select 
                                    value={task.status}
                                    onChange={(e) => updateTaskStatus(task.task_id, e.target.value)}
                                    style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}>
                                    <option value="todo">To Do</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="review">Review</option>
                                    <option value="completed">Completed</option>
                                    <option value="blocked">Blocked</option>
                                  </select>
                                  <div style={{ display: 'flex', gap: '8px' }}>
                                    <button onClick={() => editTask(task)} style={{ border: 'none', background: 'transparent', color: '#2563eb', cursor: 'pointer', textDecoration: 'underline', fontSize: '12px' }}>
                                      edit
                                    </button>
                                    <button onClick={() => deleteTask(task.task_id)} style={{ border: 'none', background: 'transparent', color: '#dc2626', cursor: 'pointer', textDecoration: 'underline', fontSize: '12px' }}>
                                      delete
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Project Advisor */}
          <div style={{ background: 'linear-gradient(160deg, #ffffff, #ecfdf5)', padding: '24px', borderRadius: '12px', border: '1px solid #86efac' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>🤖 AI Project Advisor</h3>
              <button onClick={onRefreshAI} disabled={loadingAI} style={{ padding: '8px 16px', background: 'linear-gradient(90deg, #c4b5fd, #818cf8)', color: '#1e1b4b', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '700' }}>
                {loadingAI ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {loadingAI ? (
              <p style={{ color: '#999' }}>Analyzing...</p>
            ) : !aiRecommendations ? (
              <div style={{ background: '#fff3e0', padding: '16px', borderRadius: '4px' }}>
                AI not configured
              </div>
            ) : (
              <>
                {aiRecommendations.overall_guidance && (
                  <div style={{ background: '#f3e5f5', padding: '16px', borderRadius: '8px', marginBottom: '16px', border: '1px solid #e9d5ff' }}>
                    <h4 style={{ margin: '0 0 8px 0', color: '#6a1b9a' }}>💡 Strategic Guidance</h4>
                    <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6' }}>{aiRecommendations.overall_guidance}</p>
                  </div>
                )}

                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ margin: '0 0 12px 0' }}>⭐ Recommended Actions</h4>
                  {(aiRecommendations.priority_tasks?.length > 0 || aiRecommendations.recommended_tasks?.length > 0) ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {(aiRecommendations.priority_tasks || aiRecommendations.recommended_tasks || []).slice(0, 5).map((task, idx) => (
                        <div key={idx} style={{ padding: '12px', background: '#f9f9f9', borderRadius: '4px', borderLeft: '3px solid #5b63f4' }}>
                          <div style={{ fontWeight: '500' }}>{task.task_name}</div>
                          <div style={{ fontSize: '13px', color: '#666' }}>{task.reasoning || task.reason || 'AI-prioritized task'}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#999' }}>All tasks on track</p>
                  )}
                </div>

                {aiRecommendations.resource_plan && (
                  <div style={{ background: '#ecfdf5', border: '1px solid #86efac', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
                    <h4 style={{ margin: '0 0 10px 0', color: '#14532d' }}>🧰 Resource Plan</h4>
                    <div style={{ fontSize: '14px', marginBottom: '6px' }}>
                      <strong>Crew:</strong> {aiRecommendations.resource_plan.recommended_crew_size || 'Not specified'}
                    </div>
                    <div style={{ fontSize: '14px', marginBottom: '6px' }}>
                      <strong>Equipment:</strong> {Array.isArray(aiRecommendations.resource_plan.next_equipment_needed)
                        ? (aiRecommendations.resource_plan.next_equipment_needed.join(', ') || 'Not specified')
                        : (aiRecommendations.resource_plan.next_equipment_needed || 'Not specified')}
                    </div>
                    <div style={{ fontSize: '14px' }}>
                      <strong>Upcoming Budget:</strong> {aiRecommendations.resource_plan.upcoming_tasks_budget_estimate || 'Not specified'}
                    </div>
                  </div>
                )}

                {(aiRecommendations.upcoming_tasks || []).length > 0 && (
                  <div style={{ background: '#ecfeff', border: '1px solid #99f6e4', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
                    <h4 style={{ margin: '0 0 10px 0', color: '#134e4a' }}>📌 Upcoming Tasks & Budget</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {aiRecommendations.upcoming_tasks.slice(0, 5).map((task, idx) => (
                        <div key={idx} style={{ background: 'white', border: '1px solid #ccfbf1', borderRadius: '6px', padding: '8px' }}>
                          <div style={{ fontWeight: '600', fontSize: '13px' }}>{task.task_name}</div>
                          <div style={{ fontSize: '12px', color: '#0f766e' }}>
                            {task.target_phase || 'Next phase'} · {task.budget_estimate || 'Budget TBD'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ borderTop: '1px solid #e0e0e0', paddingTop: '14px' }}>
                  <h4 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>How The Inputs Work</h4>
                  <div style={{ fontSize: '13px', color: '#475569', lineHeight: '1.6' }}>
                    <div><strong>Daily Update notes:</strong> AI reads contractor notes, updates task status and phase completion.</div>
                    <div><strong>Project Files + Analyze Selected:</strong> AI reads selected documents and creates/updates granular phase tasks.</div>
                    <div><strong>AI Instruction:</strong> optional direction for analysis style (priority order, focus area, exclusions).</div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR - Weather */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ background: 'linear-gradient(165deg, #ffffff, #ecfeff)', padding: '24px', borderRadius: '12px', position: 'sticky', top: '20px', border: '1px solid #a5f3fc' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>☀️ Weather</h3>
              <button onClick={onRefreshWeather} disabled={loadingWeather} style={{ padding: '6px 12px', background: '#f0f0f0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                {loadingWeather ? '...' : 'Refresh'}
              </button>
            </div>

            {loadingWeather ? (
              <p style={{ color: '#999' }}>Loading...</p>
            ) : !weather ? (
              <p style={{ color: '#999' }}>Weather unavailable</p>
            ) : (
              <>
                {weather.current && (
                  <div style={{ marginBottom: '20px', textAlign: 'center', padding: '20px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: '8px', color: 'white' }}>
                    <div style={{ fontSize: '14px', marginBottom: '8px', opacity: 0.9 }}>Columbia, TN</div>
                    <div style={{ fontSize: '48px', fontWeight: '600' }}>
                      {weather.current.temperature}°F
                    </div>
                    <div style={{ fontSize: '16px', marginTop: '4px', opacity: 0.9 }}>
                      {weather.current.conditions}
                    </div>
                    {weather.current.humidity && (
                      <div style={{ fontSize: '13px', marginTop: '12px', opacity: 0.8 }}>
                        💧 {weather.current.humidity}% &nbsp; 💨 {weather.current.wind_speed || 0} mph
                      </div>
                    )}
                  </div>
                )}

                {weather.recommendations && weather.recommendations.length > 0 && (
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '14px', margin: '0 0 12px 0' }}>Recommended Tasks:</h4>
                    {weather.recommendations.map((rec, idx) => (
                      <div key={idx} style={{ marginBottom: '12px', padding: '10px', background: '#f9f9f9', borderRadius: '4px' }}>
                        <div style={{ fontWeight: '600', fontSize: '13px', marginBottom: '6px', color: '#5b63f4' }}>{rec.day}</div>
                        <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px' }}>
                          {rec.tasks.map((task, tidx) => (
                            <li key={tidx}>{task}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {weather.forecast && weather.forecast.length > 0 && (
                  <>
                    <h4 style={{ fontSize: '14px', margin: '0 0 12px 0' }}>3-Day Forecast:</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {weather.forecast.slice(0, 3).map((day, idx) => (
                        <div key={idx} style={{ padding: '14px', background: '#f9f9f9', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <span style={{ fontSize: '14px', fontWeight: '600' }}>{getDayName(day, idx)}</span>
                            <span style={{ fontSize: '20px', fontWeight: '600', color: '#1976d2' }}>{day.temperature}°F</span>
                          </div>
                          <div style={{ fontSize: '13px', color: '#666' }}>{day.conditions}</div>
                          {day.precipitation_chance > 0 && (
                            <div style={{ fontSize: '12px', color: '#2196f3', marginTop: '4px' }}>
                              💧 {day.precipitation_chance}% rain
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
