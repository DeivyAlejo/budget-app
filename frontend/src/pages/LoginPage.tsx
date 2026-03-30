import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { TokenResponse } from '../types/api'

const schema = z.object({
  email: z.email('Enter a valid email'),
  password: z.string().min(8, 'Password must have at least 8 characters'),
})

type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
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
    } catch {
      setError('root', { message: 'Invalid email or password' })
    }
  })

  return (
    <main className="page auth-page">
      <h1>Welcome Back</h1>
      <form onSubmit={onSubmit} className="card form-grid">
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
