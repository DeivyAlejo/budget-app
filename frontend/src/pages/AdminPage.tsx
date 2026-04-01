import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import type { InviteCode, InviteCodeCreateResponse, PendingUser, User } from '../types/api'
import { formatDisplayDate } from '../utils/dateFormat'

export default function AdminPage() {
  const queryClient = useQueryClient()
  const [count, setCount] = useState(1)
  const [length, setLength] = useState(12)
  const [latestGenerated, setLatestGenerated] = useState<string[]>([])

  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await apiClient.get<User>('/auth/me')).data,
  })

  const pendingUsersQuery = useQuery({
    queryKey: ['admin', 'pending-users'],
    queryFn: async () => (await apiClient.get<PendingUser[]>('/admin/pending-users')).data,
    enabled: !!meQuery.data?.is_admin,
  })

  const inviteCodesQuery = useQuery({
    queryKey: ['admin', 'invite-codes'],
    queryFn: async () => (await apiClient.get<InviteCode[]>('/admin/invite-codes?include_used=false')).data,
    enabled: !!meQuery.data?.is_admin,
  })

  const approveUser = useMutation({
    mutationFn: async (userId: number) => apiClient.post(`/admin/pending-users/${userId}/approve`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'pending-users'] })
    },
  })

  const createCodes = useMutation({
    mutationFn: async () =>
      (await apiClient.post<InviteCodeCreateResponse>('/admin/invite-codes', { count, length })).data,
    onSuccess: async (data) => {
      setLatestGenerated(data.codes)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'invite-codes'] })
    },
  })

  if (meQuery.isLoading) {
    return <main className="page"><p>Loading admin panel...</p></main>
  }

  if (!meQuery.data?.is_admin) {
    return (
      <main className="page auth-page">
        <h1>Admin Access Required</h1>
        <p className="muted">Your account is not in ADMIN_EMAILS.</p>
        <p><Link to="/dashboard">Back to dashboard</Link></p>
      </main>
    )
  }

  return (
    <main className="page dashboard-page">
      <header className="toolbar card">
        <h1>Admin Panel</h1>
        <div className="toolbar-actions">
          <Link className="button-link" to="/dashboard">Back to dashboard</Link>
        </div>
      </header>

      <section className="card form-grid">
        <h2>Create One-Time Invite Codes</h2>
        <label>
          Number of codes
          <input type="number" min={1} max={50} value={count} onChange={(e) => setCount(Number(e.target.value))} />
        </label>
        <label>
          Code length
          <input type="number" min={8} max={32} value={length} onChange={(e) => setLength(Number(e.target.value))} />
        </label>
        <button onClick={() => createCodes.mutate()} disabled={createCodes.isPending}>
          {createCodes.isPending ? 'Generating...' : 'Generate codes'}
        </button>

        {latestGenerated.length > 0 && (
          <div>
            <p><strong>New codes</strong> (share privately):</p>
            <ul className="list">
              {latestGenerated.map((code) => (
                <li key={code}>{code}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Pending Accounts</h2>
        {pendingUsersQuery.data?.length ? (
          <ul className="list">
            {pendingUsersQuery.data.map((user) => (
              <li key={user.id}>
                <span>{user.email}</span>
                <span>{user.full_name || 'No name'}</span>
                <span>{formatDisplayDate(user.created_at)}</span>
                <button
                  type="button"
                  onClick={() => approveUser.mutate(user.id)}
                  disabled={approveUser.isPending}
                >
                  Approve
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No pending users.</p>
        )}
      </section>

      <section className="card">
        <h2>Unused Invite Codes</h2>
        {inviteCodesQuery.data?.length ? (
          <ul className="list">
            {inviteCodesQuery.data.map((item) => (
              <li key={item.id}>
                <span>{item.code}</span>
                <span>Created {formatDisplayDate(item.created_at)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No unused invite codes.</p>
        )}
      </section>
    </main>
  )
}
