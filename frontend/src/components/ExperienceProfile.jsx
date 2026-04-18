import React, { useState, useEffect } from 'react';
import SkillInput from './SkillInput';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const ExperienceProfile = ({ onAnalyze, isLoading, currentUser }) => {
  const [userExperience, setUserExperience] = useState({
    yearsOfExperience: 0,
    experienceType: 'Fresher',
    domain: 'Frontend',
    skillsUsed: [],
    projectLevel: 'Basic',
    confidence: 3
  });

  const [githubProjects, setGithubProjects] = useState([]);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [newProject, setNewProject] = useState({ repo_name: '', repo_url: '' });
  const [projectError, setProjectError] = useState('');

  useEffect(() => {
    if (currentUser?.user_id) {
      fetch(`${API}/github-projects/${currentUser.user_id}`)
        .then(res => res.json())
        .then(data => setGithubProjects(data))
        .catch(err => console.error("Could not fetch projects:", err));
    }
  }, [currentUser]);

  const handleExpChange = (e) => {
    setUserExperience(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleAddProject = async () => {
    setProjectError('');
    if (!newProject.repo_url.toLowerCase().includes('github.com')) {
      setProjectError('URL must be a valid GitHub link.');
      return;
    }
    if (newProject.repo_name.trim() && currentUser?.user_id) {
      try {
        const res = await fetch(`${API}/github-projects`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUser.user_id,
            repo_name: newProject.repo_name,
            repo_url: newProject.repo_url
          })
        });
        if (!res.ok) {
          const data = await res.json();
          setProjectError(data.detail || 'Failed to check project.');
          return;
        }
        const added = await res.json();
        setGithubProjects(prev => [added, ...prev]);
        setNewProject({ repo_name: '', repo_url: '' });
        setShowProjectForm(false);
      } catch (err) {
        setProjectError('Failed to add project');
      }
    }
  };

  const handleAnalyzeSkills = (skills) => {
    // skills from SkillInput
    const exp = { ...userExperience, skillsUsed: skills };
    setUserExperience(exp);
    onAnalyze(exp, githubProjects);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="glass p-6 animate-slide-up">
        <h2 className="text-xl font-semibold text-white mb-4">Your Experience Profile</h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Years of Experience</label>
            <input 
              type="number" 
              name="yearsOfExperience" 
              value={userExperience.yearsOfExperience} 
              onChange={handleExpChange} 
              min="0"
              className="w-full rounded-xl bg-slate-900/80 border border-white/[0.06] p-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-colors" 
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Experience Type</label>
            <select 
              name="experienceType" 
              value={userExperience.experienceType} 
              onChange={handleExpChange}
              className="w-full rounded-xl bg-slate-900/80 border border-white/[0.06] p-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-colors"
            >
              <option value="Fresher">Fresher</option>
              <option value="Internship">Internship</option>
              <option value="Full-time">Full-time</option>
              <option value="Freelance">Freelance</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Domain</label>
            <select 
              name="domain" 
              value={userExperience.domain} 
              onChange={handleExpChange}
              className="w-full rounded-xl bg-slate-900/80 border border-white/[0.06] p-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-colors"
            >
              <option value="Frontend">Frontend</option>
              <option value="Backend">Backend</option>
              <option value="AI/ML">AI/ML</option>
              <option value="Full Stack">Full Stack</option>
            </select>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2 border-t border-slate-700/50 pt-4">
            <h3 className="text-sm font-semibold text-white">GitHub Projects</h3>
            <button 
              type="button" 
              onClick={() => setShowProjectForm(!showProjectForm)}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              + Add Project
            </button>
          </div>
          
          {githubProjects.length > 0 && (
            <div className="space-y-3 mb-4">
              {githubProjects.map((p, i) => (
                <div key={i} className="flex justify-between items-center rounded-xl border border-white/[0.06] bg-slate-900/50 p-4 transition-colors hover:border-indigo-500/20">
                  <p className="text-sm font-semibold text-white">{p.repo_name}</p>
                  <a href={p.repo_url} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:text-indigo-300 underline">
                    GitHub Link
                  </a>
                </div>
              ))}
            </div>
          )}

          {showProjectForm && (
            <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4 space-y-3 animate-slide-up">
              {projectError && <p className="text-xs text-rose-400">{projectError}</p>}
              <input type="text" placeholder="Repo Name" className="w-full rounded-lg bg-slate-900/80 border border-white/[0.06] p-2.5 text-sm text-white outline-none focus:border-indigo-500/50" value={newProject.repo_name} onChange={(e) => setNewProject({...newProject, repo_name: e.target.value})} />
              <input type="text" placeholder="GitHub URL" className="w-full rounded-lg bg-slate-900/80 border border-white/[0.06] p-2.5 text-sm text-white outline-none focus:border-indigo-500/50" value={newProject.repo_url} onChange={(e) => setNewProject({...newProject, repo_url: e.target.value})} />
              
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setShowProjectForm(false)} className="text-xs text-slate-400 hover:text-white">Cancel</button>
                <button type="button" onClick={handleAddProject} className="btn-primary text-xs px-4 py-2">Add Project</button>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-700/50 pt-5">
          <h3 className="text-sm font-semibold text-white mb-4">Final Step: Add Skills & Analyze</h3>
          <SkillInput onAnalyze={handleAnalyzeSkills} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default ExperienceProfile;
