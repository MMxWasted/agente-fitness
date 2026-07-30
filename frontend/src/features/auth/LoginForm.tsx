import { useState, type FormEvent } from 'react'

interface LoginFormProps {
  isSubmitting: boolean
  onSubmit: (email: string, password: string) => Promise<void>
}

export function LoginForm({ isSubmitting, onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void onSubmit(email.trim(), password)
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="email">Correo electrónico</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.currentTarget.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          minLength={15}
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.currentTarget.value)}
        />
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Iniciando sesión…' : 'Iniciar sesión'}
      </button>
    </form>
  )
}
