import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'

import { apiClient } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { TokenResponse } from '../types/api'

const schema = z.object({
  email: z.email('Enter a valid email'),
  password: z.string().min(8, 'Password must have at least 8 characters'),
})

type FormValues = z.infer<typeof schema>
type LoginLocationState = { info?: string }

export default function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const stateInfo = (location.state as LoginLocationState | null)?.info
  const approvedFromLink = new URLSearchParams(location.search).get('approved') === '1'
  const infoMessage =
    stateInfo ||
    (approvedFromLink ? 'Account approved. You can sign in now.' : undefined)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = handleSubmit(async (values) => {
    try {
      const response = await apiClient.post<TokenResponse>('/auth/login', values)
      login(response.data.access_token)
      navigate('/dashboard')
    } catch (error) {
      if (isAxiosError(error)) {
        const statusCode = error.response?.status
        const detail = error.response?.data?.detail
        if (typeof detail === 'string' && detail.length > 0) {
          setError('root', {
            message: statusCode ? `${statusCode}: ${detail}` : detail,
          })
          return
        }
      }
      setError('root', { message: 'Invalid email or password' })
    }
  })

  return (
    <main className="page auth-page">
      <h1>Welcome Back</h1>
      <form onSubmit={onSubmit} className="card form-grid">
        {infoMessage && <p className="success-message">{infoMessage}</p>}
        <label>
          Email
          <input type="email" {...register('email')} />
          {errors.email && <small className="error">{errors.email.message}</small>}
        </label>
        <label>
          Password
          <input type="password" {...register('password')} />
          {errors.password && <small className="error">{errors.password.message}</small>}
        </label>
        {errors.root && <p className="error">{errors.root.message}</p>}
        <button disabled={isSubmitting} type="submit">
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <p>
        No account yet? <Link to="/register">Create one</Link>
      </p>
    </main>
  )
}
