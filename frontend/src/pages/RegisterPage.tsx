import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { isAxiosError } from 'axios'
import { Link, useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'

const authSchema = z.object({
  email: z.email('Enter a valid email'),
  password: z.string().min(8, 'Password must have at least 8 characters'),
  full_name: z.string().min(2, 'Name is too short').optional(),
  invite_code: z.string().optional(),
})

type FormValues = z.infer<typeof authSchema>

export default function RegisterPage() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(authSchema) })

  const onSubmit = handleSubmit(async (values) => {
    try {
      const payload = {
        ...values,
        invite_code: values.invite_code?.trim() || undefined,
      }

      const response = await apiClient.post('/auth/register', payload)

      if (response.data?.pending_approval) {
        navigate('/login', {
          state: {
            info:
              'Account created. An admin approval is required before you can sign in.',
          },
        })
        return
      }

      navigate('/login', {
        state: {
          info: 'Account created successfully. You can sign in now.',
        },
      })
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

      setError('root', { message: 'Could not create account' })
    }
  })

  return (
    <main className="page auth-page">
      <h1>Create Account</h1>
      <form onSubmit={onSubmit} className="card form-grid">
        <label>
          Full name
          <input {...register('full_name')} />
        </label>
        <label>
          Invite code (if required)
          <input {...register('invite_code')} />
        </label>
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
          {isSubmitting ? 'Creating...' : 'Create account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </main>
  )
}
