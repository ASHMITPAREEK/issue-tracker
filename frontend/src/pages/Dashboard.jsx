import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [projects, setProjects] = useState([])
  const [error, setError] = useState('')
  const [showArchived, setShowArchived] = useState(false)

  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const [createError, setCreateError] = useState('')
  const [creating, setCreating] = useState(false)

  async function loadData(includeArchived = showArchived) {
    setError('')
    try {
      const [statsData, projectsData] = await Promise.all([
        api.getDashboardStats(),
        api.listProjects(includeArchived),
      ])
      setStats(statsData)
      setProjects(projectsData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showArchived])

  async function handleCreateProject(e) {
    e.preventDefault()
    setCreateError('')

    if (!newProjectName.trim()) {
      setCreateError('Project name is required')
      return
    }

    setCreating(true)
    try {
      await api.createProject({
        name: newProjectName.trim(),
        description: newProjectDescription.trim() || null,
      })
      setNewProjectName('')
      setNewProjectDescription('')
      await loadData()
    } catch (err) {
      setCreateError(err.message)
    } finally {
      setCreating(false)
    }
  }

  async function handleArchiveToggle(project) {
    try {
      if (project.is_archived) {
        await api.unarchiveProject(project.id)
      } else {
        await api.archiveProject(project.id)
      }
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <h1>Dashboard</h1>

      {error && <div className="form-error" data-testid="dashboard-error">{error}</div>}

      <div className="stats-grid" data-testid="dashboard-stats">
        <StatCard label="Total Projects" value={stats?.total_projects} testId="stat-total-projects" />
        <StatCard label="Total Issues" value={stats?.total_issues} testId="stat-total-issues" />
        <StatCard label="Open Issues" value={stats?.open_issues} testId="stat-open-issues" />
        <StatCard label="Completed Issues" value={stats?.completed_issues} testId="stat-completed-issues" />
      </div>

      <section className="section">
        <h2>Create Project</h2>
        <form onSubmit={handleCreateProject} className="inline-form" data-testid="create-project-form">
          {createError && <div className="form-error" data-testid="create-project-error">{createError}</div>}
          <label>
            Name
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              data-testid="project-name-input"
            />
          </label>
          <label>
            Description
            <input
              type="text"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
              data-testid="project-description-input"
            />
          </label>
          <button type="submit" disabled={creating} data-testid="create-project-submit">
            {creating ? 'Creating...' : 'Create Project'}
          </button>
        </form>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>Projects</h2>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              data-testid="show-archived-toggle"
            />
            Show archived
          </label>
        </div>

        <ul className="project-list" data-testid="project-list">
          {projects.map((project) => (
            <li key={project.id} className="project-list-item" data-testid={`project-item-${project.id}`}>
              <Link to={`/projects/${project.id}`}>{project.name}</Link>
              {project.is_archived && <span className="badge">Archived</span>}
              <span className="muted"> · {project.issue_count} issue(s)</span>
              <button
                onClick={() => handleArchiveToggle(project)}
                data-testid={`archive-toggle-${project.id}`}
              >
                {project.is_archived ? 'Unarchive' : 'Archive'}
              </button>
            </li>
          ))}
          {projects.length === 0 && <li className="muted">No projects yet.</li>}
        </ul>
      </section>
    </div>
  )
}

function StatCard({ label, value, testId }) {
  return (
    <div className="stat-card" data-testid={testId}>
      <div className="stat-value">{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
