import { useState, useEffect, useRef } from 'react';
import './App.css';

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
        setProjectDetails(data);
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

// Helper function to get day name
function getDayName(day, index) {
  if (!day || !day.date) {
    // Fallback based on index
    const today = new Date();
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() + index);
    
    if (index === 0) return 'Today';
    if (index === 1) return 'Tomorrow';
    return targetDate.toLocaleDateString('en-US', { weekday: 'long' });
  }
  
  // Parse the actual date from weather data
  const forecastDate = new Date(day.date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  forecastDate.setHours(0, 0, 0, 0);
  
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  const diffDays = Math.floor((forecastDate - today) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  return forecastDate.toLocaleDateString('en-US', { weekday: 'long' });
}

// Project Detail Component - FULLY FIXED
