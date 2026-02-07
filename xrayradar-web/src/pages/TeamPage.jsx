import { useState, useCallback, useEffect } from 'react'
import { fetchJson } from '../utils/api'

export function TeamPage({ me }) {
  const [members, setMembers] = useState([])
  const [invites, setInvites] = useState([])
  const [projects, setProjects] = useState([])
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteProjectIds, setInviteProjectIds] = useState([])
  const [addMemberProjectId, setAddMemberProjectId] = useState('')
  const [addMemberEmail, setAddMemberEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const [membersData, invitesData, projectsData] = await Promise.all([
        fetchJson('/api/user/team/members').catch(() => []),
        fetchJson('/api/user/team/invites').catch(() => []),
        fetchJson('/api/user/projects').catch(() => []),
      ])
      setMembers(Array.isArray(membersData) ? membersData : [])
      setInvites(Array.isArray(invitesData) ? invitesData : [])
      setProjects(Array.isArray(projectsData) ? projectsData : [])
    } catch (e) {
      setError(e.message || 'Failed to load team')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const projectIdToName = (id) => {
    const p = projects.find((x) => x.id === id)
    return p ? p.name : `Project ${id}`
  }

  const sendInvite = async (e) => {
    e.preventDefault()
    if (busy) return
    const email = inviteEmail.trim().toLowerCase()
    if (!email) {
      setError('Email is required')
      return
    }
    if (inviteProjectIds.length === 0) {
      setError('Select at least one project')
      return
    }
    setBusy(true)
    setError('')
    try {
      await fetchJson('/api/user/team/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, project_ids: inviteProjectIds }),
      })
      setInviteEmail('')
      setInviteProjectIds([])
      await load()
    } catch (e2) {
      setError(e2.message || 'Failed to send invite')
    } finally {
      setBusy(false)
    }
  }

  const addMemberToProject = async (e) => {
    e.preventDefault()
    if (busy) return
    const projectId = addMemberProjectId ? Number(addMemberProjectId) : null
    const email = addMemberEmail.trim().toLowerCase()
    if (!projectId || !email) {
      setError('Project and email are required')
      return
    }
    setBusy(true)
    setError('')
    try {
      await fetchJson(`/api/user/projects/${projectId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      setAddMemberProjectId('')
      setAddMemberEmail('')
      await load()
    } catch (e2) {
      setError(e2.message || 'Failed to add member')
    } finally {
      setBusy(false)
    }
  }

  const revokeProjectAccess = async (memberUserId, projectId) => {
    try {
      setError('')
      await fetchJson(`/api/user/projects/${projectId}/members/${memberUserId}`, { method: 'DELETE' })
      await load()
    } catch (e) {
      setError(e.message || 'Failed to revoke access')
    }
  }

  const removeFromTeam = async (memberUserId) => {
    if (!window.confirm('Remove this user from all your projects?')) return
    try {
      setError('')
      await fetchJson(`/api/user/team/members/${memberUserId}`, { method: 'DELETE' })
      await load()
    } catch (e) {
      setError(e.message || 'Failed to remove member')
    }
  }

  const toggleInviteProject = (id) => {
    setInviteProjectIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  return (
    <div className="container page">
      <header className="pageHeader">
        <h1 className="pageTitle">Team</h1>
        <p className="pageSubtitle">
          Invite members and assign them to projects (Teams plans only).
        </p>
      </header>

      {error ? (
        <div className="fieldError" role="alert" style={{ marginBottom: 16 }}>
          {error}
        </div>
      ) : null}

      <section className="pageSection">
        <h2 className="pageSectionTitle">Invite by email</h2>
        <form onSubmit={sendInvite} className="pageForm">
          <div className="pageFormRow">
            <div style={{ flex: 1, minWidth: 200 }}>
              <label className="fieldLabel">Email</label>
              <input
                className="fieldInput"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="teammate@example.com"
                style={{ marginTop: 6 }}
              />
            </div>
          </div>
          <div className="pageFormRow" style={{ marginTop: 12 }}>
            <label className="fieldLabel">Projects to grant access to</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
              {projects.map((p) => (
                <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={inviteProjectIds.includes(p.id)}
                    onChange={() => toggleInviteProject(p.id)}
                  />
                  {p.name}
                </label>
              ))}
            </div>
          </div>
          <button className="button buttonPrimary" type="submit" disabled={busy} style={{ marginTop: 12 }}>
            Send invite
          </button>
        </form>
      </section>

      <section className="pageSection">
        <h2 className="pageSectionTitle">Add member to project</h2>
        <form onSubmit={addMemberToProject} className="pageForm">
          <div className="pageFormRow" style={{ flexWrap: 'wrap', gap: 12 }}>
            <div style={{ minWidth: 180 }}>
              <label className="fieldLabel">Project</label>
              <select
                className="fieldInput"
                value={addMemberProjectId}
                onChange={(e) => setAddMemberProjectId(e.target.value)}
                style={{ marginTop: 6, width: '100%' }}
              >
                <option value="">Select project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div style={{ minWidth: 220 }}>
              <label className="fieldLabel">Email</label>
              <input
                className="fieldInput"
                type="email"
                value={addMemberEmail}
                onChange={(e) => setAddMemberEmail(e.target.value)}
                placeholder="user@example.com"
                style={{ marginTop: 6 }}
              />
            </div>
            <button className="button buttonPrimary" type="submit" disabled={busy} style={{ alignSelf: 'flex-end' }}>
              Add
            </button>
          </div>
        </form>
      </section>

      {invites.length > 0 && (
        <section className="pageSection">
          <h2 className="pageSectionTitle">Pending invites</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {invites.map((inv) => (
              <li key={inv.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <strong>{inv.email}</strong> — {inv.project_ids.map(projectIdToName).join(', ')}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="pageSection">
        <h2 className="pageSectionTitle">Team members</h2>
        {members.length === 0 ? (
          <p className="pageCardText">No team members yet. Invite someone or add a user to a project.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="pageTable">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Projects</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.user_id}>
                    <td>{m.email}</td>
                    <td>
                      {m.project_ids.map((pid) => (
                        <span key={pid} style={{ display: 'inline-block', marginRight: 8 }}>
                          {projectIdToName(pid)}
                          <button
                            type="button"
                            className="button"
                            style={{ marginLeft: 4, padding: '2px 6px', fontSize: 11 }}
                            onClick={() => revokeProjectAccess(m.user_id, pid)}
                          >
                            Revoke
                          </button>
                        </span>
                      ))}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="button"
                        onClick={() => removeFromTeam(m.user_id)}
                      >
                        Remove from team
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
