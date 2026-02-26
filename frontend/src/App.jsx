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
  const [uploadingFiles, setUploadingFiles] = useState(false);
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
  await loadProjectDetails(project.project_id);
  await loadWeather();
  await loadAIRecommendations(project.project_id);
  await loadProjectFiles(project.project_id); // ADD THIS LINE
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
    loadProjectFiles(selectedProject.project_id); // ADD THIS LINE
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
    }
  } catch (err) {
    console.error('Error loading files:', err);
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
      alert(`✅ Success!\n\n📁 ${result.files_uploaded} files uploaded\n🤖 ${result.tasks_generated} tasks generated by AI\n\nRefreshing project...`);
      
      await loadProjectFiles(selectedProject.project_id);
      await loadProjectDetails(selectedProject.project_id);
      await loadAIRecommendations(selectedProject.project_id);
    } else {
      const error = await response.json();
      alert(`Error: ${error.detail || 'Upload failed'}`);
    }
  } catch (err) {
    console.error('Upload error:', err);
    alert('Error uploading files. Please try again.');
  } finally {
    setUploadingFiles(false);
    event.target.value = '';
  }
};

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
  user={user}
  onBack={() => setSelectedProject(null)}
  onRefresh={refreshProject}
  onRefreshWeather={loadWeather}
  onRefreshAI={() => loadAIRecommendations(selectedProject.project_id)}
  projectFiles={projectFiles}
  showFilesPanel={showFilesPanel}
  setShowFilesPanel={setShowFilesPanel}
  uploadingFiles={uploadingFiles}
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
function LoginPage({ email, setEmail, password, setPassword, onLogin, error, backendConnected }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
      <div style={{ background: 'white', padding: '40px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', maxWidth: '400px', width: '100%' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '10px' }}>Land Development Tracker</h1>
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
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{ background: 'white', borderBottom: '1px solid #e0e0e0', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>Land Development Tracker</h1>
          <button style={{ padding: '8px 16px', background: '#f0f0f0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Dashboard
          </button>
        </div>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer" style={{ color: '#5b63f4', textDecoration: 'none' }}>
            API Docs →
          </a>
          <button onClick={onLogout} style={{ padding: '8px 20px', background: '#5b63f4', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </div>

      <div style={{ padding: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h2 style={{ margin: 0 }}>Your Projects</h2>
          <button onClick={onRefresh} style={{ padding: '8px 20px', background: '#f0f0f0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Refresh
          </button>
        </div>

        {projects.length === 0 ? (
          <div style={{ background: 'white', padding: '60px', textAlign: 'center', borderRadius: '8px', color: '#999' }}>
            No projects found
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {projects.map(project => (
              <div key={project.project_id} onClick={() => onSelectProject(project)} style={{ background: 'white', padding: '24px', borderRadius: '8px', cursor: 'pointer', border: '1px solid #e0e0e0', transition: 'box-shadow 0.2s' }} 
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                  <div>
                    <h3 style={{ margin: '0 0 8px 0' }}>{project.project_name}</h3>
                    <span style={{ fontSize: '14px', color: '#666' }}>{project.project_code}</span>
                  </div>
                  <span style={{ background: project.status === 'in_progress' ? '#e3f2fd' : '#f0f0f0', color: project.status === 'in_progress' ? '#1976d2' : '#666', padding: '4px 12px', borderRadius: '12px', fontSize: '12px' }}>
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
  aiRecommendations, loadingAI, apiUrl, token, user, 
  onBack, onRefresh, onRefreshWeather, onRefreshAI,
  projectFiles, showFilesPanel, setShowFilesPanel,
  uploadingFiles, handleFileUpload, deleteFile,
  fileInputRef, getDayName
}) {
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [phaseTasks, setPhaseTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiChatHistory, setAiChatHistory] = useState([]);
  const [loadingAiChat, setLoadingAiChat] = useState(false);
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

  const askAI = async () => {
    if (!aiQuestion.trim()) return;
    
    setLoadingAiChat(true);
    const userMessage = { role: 'user', content: aiQuestion };
    setAiChatHistory([...aiChatHistory, userMessage]);
    setAiQuestion('');
    
    try {
      const response = await fetch(`${apiUrl}/api/ai/recommendations/${project.project_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        const answer = data.overall_guidance || 'Based on current project status, I recommend focusing on the priority tasks.';
        setAiChatHistory(prev => [...prev, { role: 'assistant', content: answer }]);
      }
    } catch (err) {
      setAiChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, error occurred.' }]);
    }
    
    setLoadingAiChat(false);
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
          message: result.message || 'Daily update submitted!',
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
        setUpdateResult({ success: false, message: 'Error submitting update' });
      }
    } catch (err) {
      setUpdateResult({ success: false, message: 'Error submitting update' });
    }
    
    setSubmittingUpdate(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Header */}
      <div style={{ background: 'white', borderBottom: '1px solid #e0e0e0', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <button onClick={onBack} style={{ padding: '10px 20px', background: '#e8e8e8', border: '2px solid #999', borderRadius: '6px', cursor: 'pointer', color: '#000', fontWeight: '600', fontSize: '15px' }}>
            ← Back
          </button>
          <h1 style={{ margin: 0, fontSize: '24px' }}>{project.project_name}</h1>
          <span style={{ fontSize: '14px', color: '#666' }}>{project.project_code}</span>
        </div>
        <button onClick={onRefresh} style={{ padding: '8px 20px', background: '#5b63f4', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Refresh All
        </button>
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
          </div>

          {/* Daily Update Panel */}
          {showDailyUpdate && (
            <div style={{ background: 'white', padding: '24px', borderRadius: '8px', border: '2px solid #4caf50' }}>
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
              background: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>📁 Project Files & Documents</h3>
                  <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
                    Upload plans, budgets, reports - AI will analyze and update tasks automatically
                  </p>
                </div>
                
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
                
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.xlsx,.xls,.docx,.doc,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
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
                      <th style={{ padding: '12px', textAlign: 'left' }}>Filename</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Type</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Uploaded</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>By</th>
                      <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projectFiles.map(file => (
                      <tr key={file.document_id} style={{ borderBottom: '1px solid #e9ecef' }}>
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
                        <td style={{ padding: '12px', color: '#666' }}>
                          {file.uploaded_at ? new Date(file.uploaded_at).toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', year: 'numeric'
                          }) : 'Unknown'}
                        </td>
                        <td style={{ padding: '12px', color: '#666' }}>{file.uploaded_by || 'Unknown'}</td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <button
                            onClick={() => deleteFile(file.document_id)}
                            style={{
                              padding: '6px 12px',
                              background: '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            🗑️ Delete
                          </button>
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
                      When you upload budget plans, schedules, or specifications, AI automatically:<br/>
                      • Extracts tasks and assigns them to the correct phase<br/>
                      • Sets priorities based on document content<br/>
                      • Estimates hours and identifies dependencies
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Development Phases */}
          <div style={{ background: 'white', padding: '24px', borderRadius: '8px' }}>
            <h3 style={{ margin: '0 0 20px 0' }}>Development Phases</h3>
            
            {!details?.phases || details.phases.length === 0 ? (
              <p style={{ color: '#999' }}>No phases found</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {details.phases.map(phase => (
                  <div key={phase.phase_id} style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '16px', cursor: 'pointer' }}
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
                        <h5 style={{ margin: '0 0 12px 0' }}>Tasks</h5>
                        {loadingTasks ? (
                          <p style={{ color: '#999' }}>Loading...</p>
                        ) : phaseTasks.length === 0 ? (
                          <p style={{ color: '#999' }}>No tasks</p>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {phaseTasks.map(task => (
                              <div key={task.task_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: '#f9f9f9', borderRadius: '4px' }}>
                                <div>
                                  <div style={{ fontWeight: '500' }}>{task.task_name}</div>
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
                                <select 
                                  value={task.status}
                                  onChange={(e) => updateTaskStatus(task.task_id, e.target.value)}
                                  style={{ padding: '6px', borderRadius: '4px', cursor: 'pointer' }}>
                                  <option value="todo">To Do</option>
                                  <option value="in_progress">In Progress</option>
                                  <option value="completed">Completed</option>
                                </select>
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
          <div style={{ background: 'white', padding: '24px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ margin: 0 }}>🤖 AI Project Advisor</h3>
              <button onClick={onRefreshAI} disabled={loadingAI} style={{ padding: '6px 16px', background: '#f0f0f0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
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
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ margin: '0 0 12px 0' }}>⭐ Recommended Actions</h4>
                  {aiRecommendations.recommended_tasks?.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {aiRecommendations.recommended_tasks.slice(0, 5).map((task, idx) => (
                        <div key={idx} style={{ padding: '12px', background: '#f9f9f9', borderRadius: '4px', borderLeft: '3px solid #5b63f4' }}>
                          <div style={{ fontWeight: '500' }}>{task.task_name}</div>
                          <div style={{ fontSize: '13px', color: '#666' }}>{task.reason}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#999' }}>All tasks on track</p>
                  )}
                </div>

                {aiRecommendations.overall_guidance && (
                  <div style={{ background: '#f3e5f5', padding: '16px', borderRadius: '4px', marginBottom: '20px' }}>
                    <h4 style={{ margin: '0 0 8px 0', color: '#6a1b9a' }}>💡 Strategic Guidance</h4>
                    <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6' }}>{aiRecommendations.overall_guidance}</p>
                  </div>
                )}

                <div style={{ borderTop: '1px solid #e0e0e0', paddingTop: '20px' }}>
                  <h4 style={{ margin: '0 0 12px 0' }}>💬 Ask AI</h4>
                  
                  {aiChatHistory.length > 0 && (
                    <div style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '16px', padding: '12px', background: '#f9f9f9', borderRadius: '4px' }}>
                      {aiChatHistory.map((msg, idx) => (
                        <div key={idx} style={{ marginBottom: '12px' }}>
                          <div style={{ fontWeight: '600', color: msg.role === 'user' ? '#5b63f4' : '#4caf50', fontSize: '13px' }}>
                            {msg.role === 'user' ? '👤 You:' : '🤖 AI:'}
                          </div>
                          <div style={{ fontSize: '14px', paddingLeft: '12px' }}>{msg.content}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      placeholder="What should I prioritize?"
                      value={aiQuestion}
                      onChange={(e) => setAiQuestion(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && askAI()}
                      disabled={loadingAiChat}
                      style={{ flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <button 
                      onClick={askAI}
                      disabled={loadingAiChat}
                      style={{ padding: '10px 20px', background: '#5b63f4', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                      Ask
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR - Weather */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ background: 'white', padding: '24px', borderRadius: '8px', position: 'sticky', top: '20px' }}>
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
