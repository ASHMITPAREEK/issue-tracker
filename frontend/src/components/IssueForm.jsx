import { useState } from 'react'

const STATUSES = ['Todo', 'In Progress', 'Done']
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
const TITLE_MAX_LENGTH = 200

export default function IssueForm({ users, onSubmit, onCancel, initialValues = {} }) {
  const [title, setTitle] = useState(initialValues.title || '')
  const [description, setDescription] = useState(initialValues.description || '')
  const [priority, setPriority] = useState(initialValues.priority || 'Medium')
  const [status, setStatus] = useState(initialValues.status || 'Todo')
  const [assigneeId, setAssigneeId] = useState(initialValues.assignee?.id || '')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function validate() {
    const trimmed = title.trim()
    if (!trimmed) return 'Title is required'
    if (trimmed.length > TITLE_MAX_LENGTH) {
      return `Title must be ${TITLE_MAX_LENGTH} characters or fewer`
    }
    if (!STATUSES.includes(status)) return 'Invalid status'
    if (!PRIORITIES.includes(priority)) return 'Invalid priority'
    return ''
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setError('')
    setSubmitting(true)
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim() || null,
        priority,
        status,
        assignee_id: assigneeId ? Number(assigneeId) : null,
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="issue-form" data-testid="issue-form">
      {error && <div className="form-error" data-testid="issue-form-error">{error}</div>}

      <label>
        Title
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={TITLE_MAX_LENGTH}
          data-testid="issue-title-input"
        />
      </label>

      <label>
        Description
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          data-testid="issue-description-input"
        />
      </label>

      <div className="form-row">
        <label>
          Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value)} data-testid="issue-priority-input">
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>

        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)} data-testid="issue-status-input">
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label>
          Assignee
          <select
            value={assigneeId}
            onChange={(e) => setAssigneeId(e.target.value)}
            data-testid="issue-assignee-input"
          >
            <option value="">Unassigned</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" disabled={submitting} data-testid="issue-form-submit">
          {submitting ? 'Saving...' : 'Save'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} data-testid="issue-form-cancel">
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
