import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'
import IssueForm from '../components/IssueForm'
import IssueRow from '../components/IssueRow'

const STATUSES = ['Todo', 'In Progress', 'Done']
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [issues, setIssues] = useState([])
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingIssue, setEditingIssue] = useState(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [assigneeFilter, setAssigneeFilter] = useState('')

  const loadIssues = useCallback(async () => {
    try {
      const data = await api.listIssues({
        project_id: projectId,
        search: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        assignee_id: assigneeFilter || undefined,
      })
      setIssues(data)
    } catch (err) {
      setError(err.message)
    }
  }, [projectId, search, statusFilter, priorityFilter, assigneeFilter])

  useEffect(() => {
    async function loadInitial() {
      try {
        const [projectData, usersData] = await Promise.all([
          api.getProject(projectId),
          api.users(),
        ])
        setProject(projectData)
        setUsers(usersData)
      } catch (err) {
        setError(err.message)
      }
    }
    loadInitial()
  }, [projectId])

  useEffect(() => {
    loadIssues()
  }, [loadIssues])

  async function handleCreateIssue(payload) {
    await api.createIssue({ ...payload, project_id: Number(projectId) })
    setShowForm(false)
    await loadIssues()
  }

  async function handleEditIssue(payload) {
    await api.updateIssue(editingIssue.id, payload)
    setEditingIssue(null)
    await loadIssues()
  }

  async function handleUpdate(issueId, payload) {
    try {
      await api.updateIssue(issueId, payload)
      await loadIssues()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(issueId) {
    try {
      await api.deleteIssue(issueId)
      await loadIssues()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!project) {
    return <div className="page">{error ? <div className="form-error">{error}</div> : 'Loading...'}</div>
  }

  return (
    <div className="page">
      <p><Link to="/">&larr; Back to dashboard</Link></p>
      <h1 data-testid="project-title">{project.name}</h1>
      {project.description && <p className="muted">{project.description}</p>}
      <p className="muted">Owner: {project.owner.name} · Created {new Date(project.created_at).toLocaleDateString()}</p>

      {error && <div className="form-error" data-testid="project-error">{error}</div>}

      <section className="section">
        <div className="section-header">
          <h2>Issues</h2>
          <button onClick={() => setShowForm((v) => !v)} data-testid="toggle-issue-form">
            {showForm ? 'Cancel' : 'New Issue'}
          </button>
        </div>

        {showForm && (
          <IssueForm
            users={users}
            onSubmit={handleCreateIssue}
            onCancel={() => setShowForm(false)}
          />
        )}

        {editingIssue && (
          <div data-testid="edit-issue-form-container">
            <h3>Edit Issue</h3>
            <IssueForm
              users={users}
              initialValues={editingIssue}
              onSubmit={handleEditIssue}
              onCancel={() => setEditingIssue(null)}
            />
          </div>
        )}

        <div className="filters" data-testid="issue-filters">
          <input
            type="text"
            placeholder="Search by title"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="search-input"
          />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} data-testid="status-filter">
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} data-testid="priority-filter">
            <option value="">All priorities</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <select value={assigneeFilter} onChange={(e) => setAssigneeFilter(e.target.value)} data-testid="assignee-filter">
            <option value="">All assignees</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </div>

        <table className="issue-table" data-testid="issue-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assignee</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <IssueRow
                key={issue.id}
                issue={issue}
                users={users}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
                onEdit={setEditingIssue}
              />
            ))}
            {issues.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">No issues found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
