// Enhanced Daily Update Component with AI Processing
// Replace the existing daily update section in App.jsx with this

// Add these state variables at the top of ProjectDetail component:
const [dailyUpdate, setDailyUpdate] = useState({
  notes: '',
  blockers: '',
  weatherImpact: '',
  crewSize: 10,
  equipment: ''
});
const [submittingUpdate, setSubmittingUpdate] = useState(false);
const [updateResult, setUpdateResult] = useState(null);

// Replace the submitDailyUpdate function with this enhanced version:
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
      body: JSON.stringify({
        notes: dailyUpdate.notes,
        blockers: dailyUpdate.blockers || null,
        weather_impact: dailyUpdate.weatherImpact || weather?.current?.conditions,
        crew_size: parseInt(dailyUpdate.crewSize) || null,
        equipment_available: dailyUpdate.equipment || null
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      
      // Store result to display
      setUpdateResult(result);
      
      // Update AI recommendations with new analysis
      if (result.analysis) {
        setAiRecommendations({
          ...result.analysis,
          recommended_tasks: result.analysis.next_actions?.map(action => ({
            task_name: action,
            reason: 'Based on today\'s progress'
          })) || [],
          risks: result.analysis.risks || [],
          opportunities: result.analysis.opportunities || [],
          overall_guidance: result.analysis.strategic_guidance,
          project_summary: {
            phase: result.updated_progress?.phase,
            progress: result.updated_progress?.completion
          }
        });
      }
      
      // Refresh project to show updated progress
      onRefresh();
      onRefreshAI();
      
      // Clear form
      setDailyUpdate({
        notes: '',
        blockers: '',
        weatherImpact: '',
        crewSize: 10,
        equipment: ''
      });
      
      // Show success message
      alert('✅ Daily Update Processed!\n\nAI has analyzed your update and refreshed recommendations. Check the AI Advisor section below for insights.');
    } else {
      alert('Error submitting daily update. Please try again.');
    }
  } catch (err) {
    console.error('Error submitting daily update:', err);
    alert('Error submitting daily update. Please check your connection.');
  }
  
  setSubmittingUpdate(false);
};

// Enhanced Daily Update Panel JSX (replace existing panel):
{(user?.role === 'contractor' || user?.role === 'admin') && (
  <div style={{ background: 'white', padding: '24px', borderRadius: '8px', border: '2px solid #4caf50', position: 'relative' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
      <h3 style={{ margin: 0, color: '#4caf50' }}>📝 Daily Update</h3>
      <span style={{ fontSize: '14px', color: '#666' }}>{new Date().toLocaleDateString()}</span>
    </div>
    
    {/* Main Notes */}
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#333' }}>
        What did you accomplish today? *
      </label>
      <textarea
        placeholder="E.g., Completed grading for lots 5-8, installed 200ft of water main, poured concrete foundations..."
        value={dailyUpdate.notes}
        onChange={(e) => setDailyUpdate({...dailyUpdate, notes: e.target.value})}
        disabled={submittingUpdate}
        style={{ width: '100%', minHeight: '100px', padding: '12px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px', resize: 'vertical', fontFamily: 'inherit' }}
      />
    </div>
    
    {/* Blockers */}
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#333' }}>
        Any issues or blockers?
      </label>
      <input
        type="text"
        placeholder="E.g., Waiting on permits, equipment breakdown, material delay..."
        value={dailyUpdate.blockers}
        onChange={(e) => setDailyUpdate({...dailyUpdate, blockers: e.target.value})}
        disabled={submittingUpdate}
        style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
      />
    </div>
    
    {/* Resource Info Row */}
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px', marginBottom: '16px' }}>
      <div>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#333' }}>
          Crew Size
        </label>
        <input
          type="number"
          value={dailyUpdate.crewSize}
          onChange={(e) => setDailyUpdate({...dailyUpdate, crewSize: e.target.value})}
          disabled={submittingUpdate}
          style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
        />
      </div>
      <div>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#333' }}>
          Equipment On Site
        </label>
        <input
          type="text"
          placeholder="E.g., 2 excavators, dump truck, compactor..."
          value={dailyUpdate.equipment}
          onChange={(e) => setDailyUpdate({...dailyUpdate, equipment: e.target.value})}
          disabled={submittingUpdate}
          style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
        />
      </div>
    </div>
    
    {/* Weather Impact */}
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#333' }}>
        Weather Impact
      </label>
      <input
        type="text"
        placeholder={`Current: ${weather?.current?.conditions || 'Loading...'}`}
        value={dailyUpdate.weatherImpact}
        onChange={(e) => setDailyUpdate({...dailyUpdate, weatherImpact: e.target.value})}
        disabled={submittingUpdate}
        style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px' }}
      />
    </div>
    
    {/* Submit Button */}
    <button 
      onClick={submitDailyUpdate}
      disabled={submittingUpdate || !dailyUpdate.notes.trim()}
      style={{ 
        width: '100%',
        padding: '12px 24px', 
        background: submittingUpdate ? '#ccc' : '#4caf50', 
        color: 'white', 
        border: 'none', 
        borderRadius: '4px', 
        cursor: submittingUpdate ? 'not-allowed' : 'pointer', 
        fontWeight: '500',
        fontSize: '15px'
      }}>
      {submittingUpdate ? '🤖 Processing with AI...' : '✅ Submit & Analyze with AI'}
    </button>
    
    {/* Result Display */}
    {updateResult && (
      <div style={{ marginTop: '16px', padding: '12px', background: '#e8f5e9', borderRadius: '4px', border: '1px solid #4caf50' }}>
        <div style={{ fontWeight: '600', color: '#2e7d32', marginBottom: '8px' }}>
          ✅ {updateResult.message}
        </div>
        {updateResult.analysis?.progress_assessment && (
          <div style={{ fontSize: '14px', color: '#666' }}>
            {updateResult.analysis.progress_assessment}
          </div>
        )}
      </div>
    )}
    
    <div style={{ marginTop: '12px', fontSize: '12px', color: '#999', textAlign: 'center' }}>
      💡 AI will analyze your update and provide strategic recommendations below
    </div>
  </div>
)}
