const STATUSES = ['Todo', 'In Progress', 'Done']

export default function IssueRow({ issue, users, onUpdate, onDelete, onEdit }) {
  return (
    <tr data-testid={`issue-row-${issue.id}`}>
      <td>{issue.title}</td>
      <td>
        <span className={`badge priority-${issue.priority.toLowerCase()}`}>{issue.priority}</span>
      </td>
      <td>
        <select
          value={issue.status}
          onChange={(e) => onUpdate(issue.id, { status: e.target.value })}
          data-testid={`issue-status-select-${issue.id}`}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </td>
      <td>
        <select
          value={issue.assignee?.id || ''}
          onChange={(e) =>
            onUpdate(issue.id, { assignee_id: e.target.value ? Number(e.target.value) : null })
          }
          data-testid={`issue-assignee-select-${issue.id}`}
        >
          <option value="">Unassigned</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>{u.name}</option>
          ))}
        </select>
      </td>
      <td>{new Date(issue.created_at).toLocaleDateString()}</td>
      <td>
        <button onClick={() => onEdit(issue)} data-testid={`edit-issue-${issue.id}`}>Edit</button>
        <button onClick={() => onDelete(issue.id)} data-testid={`delete-issue-${issue.id}`}>Delete</button>
      </td>
    </tr>
  )
}
