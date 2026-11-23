import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiRequest } from './services/api'
import './App.css'

type Screen =
  | 'login'
  | 'register'
  | 'loginOtp'
  | 'forgotEmail'
  | 'forgotOtp'
  | 'resetPassword'
  | 'profile'
  | 'adminLogin'
  | 'adminDashboard'

type Profile = {
  id: number
  full_name: string
  email: string
  phone: string
  is_active?: boolean
  is_logged_in?: boolean
}

function App() {
  const [screen, setScreen] = useState<Screen>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [adminPasscode, setAdminPasscode] = useState('')
  const [adminUsers, setAdminUsers] = useState<Profile[]>([])
  const [adminLoading, setAdminLoading] = useState(false)
  const [maskedPhone, setMaskedPhone] = useState('')
  const [maskedEmail, setMaskedEmail] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      loadProfile(token)
    }
  }, [])

  async function loadAdminUsers() {
    const token = sessionStorage.getItem('admin_token')
    if (!token) return
    setAdminLoading(true)
    setError('')
    try {
      const users = await apiRequest<Profile[]>('/admin/users', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setAdminUsers(users)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load user list')
    } finally {
      setAdminLoading(false)
    }
  }

  async function loadProfile(token: string) {
    setLoading(true)
    setError('')
    try {
      const result = await apiRequest<Profile>('/profile', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setProfile(result)
      setScreen('profile')
    } catch (err) {
      sessionStorage.removeItem('access_token')
      setError(err instanceof Error ? err.message : 'Unable to load profile')
      setScreen('login')
    } finally {
      setLoading(false)
    }
  }

  async function handleAdminLogin(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const result = await apiRequest<{ admin_token: string; message: string }>('/admin/login', {
        method: 'POST',
        body: JSON.stringify({ passcode: adminPasscode }),
      })
      sessionStorage.setItem('admin_token', result.admin_token)
      setScreen('adminDashboard')
      setMessage(result.message)
      const users = await apiRequest<Profile[]>('/admin/users', {
        headers: { Authorization: `Bearer ${result.admin_token}` },
      })
      setAdminUsers(users)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid admin passcode')
    } finally {
      setLoading(false)
    }
  }

  async function handleToggleBlock(userId: number) {
    const token = sessionStorage.getItem('admin_token')
    if (!token) return
    setError('')
    setMessage('')
    try {
      const res = await apiRequest<{ message: string; user_id: number; is_active: boolean; is_logged_in?: boolean }>(
        `/admin/users/${userId}/toggle-block`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      setMessage(res.message)
      setAdminUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: res.is_active, is_logged_in: res.is_logged_in ?? u.is_logged_in } : u))
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    }
  }

  function goTo(nextScreen: Screen) {
    setScreen(nextScreen)
    setError('')
    setMessage('')
  }

  async function handleLogin(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const result = await apiRequest<{
        message: string
        email_masked?: string
        phone_masked?: string
      }>('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setOtp('')
      setMaskedEmail(result.email_masked || '')
      setMaskedPhone(result.phone_masked || '')
      goTo('loginOtp')
      setMessage(result.message || `Verification code sent to ${result.email_masked || email}!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleLoginOtp(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await apiRequest<{ access_token: string }>('/verify-login-otp', {
        method: 'POST',
        body: JSON.stringify({ email, otp }),
      })
      sessionStorage.setItem('access_token', result.access_token)
      await loadProfile(result.access_token)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleForgotEmail(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await apiRequest<{
        message: string
        email_masked?: string
        phone_masked?: string
      }>('/generate-otp', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setOtp('')
      setMaskedEmail(result.email_masked || '')
      setMaskedPhone(result.phone_masked || '')
      goTo('forgotOtp')
      setMessage(result.message || `Verification code sent to ${result.email_masked || email}!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate OTP')
    } finally {
      setLoading(false)
    }
  }

  async function handleForgotOtp(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await apiRequest<{ reset_token: string }>('/verify-otp', {
        method: 'POST',
        body: JSON.stringify({ email, otp }),
      })
      setResetToken(result.reset_token)
      sessionStorage.setItem('reset_token', result.reset_token)
      setNewPassword('')
      goTo('resetPassword')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleResetPassword(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await apiRequest('/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          reset_token: resetToken,
          new_password: newPassword,
        }),
      })
      sessionStorage.removeItem('reset_token')
      setPassword('')
      setResetToken('')
      goTo('login')
      setMessage('Password reset successfully. Please log in.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password reset failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleLogout() {
    const token = sessionStorage.getItem('access_token')
    if (token) {
      try {
        await apiRequest('/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        })
      } catch {
        // Continue logout even if network fails
      }
    }
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('reset_token')
    setProfile(null)
    setAdminUsers([])
    setPassword('')
    goTo('login')
  }

  const isAuthScreen = screen !== 'profile' && screen !== 'adminDashboard'

  return (
    <main className="auth-page">
      {isAuthScreen ? (
        <section className="auth-card" aria-labelledby="auth-title">
          <h1 id="auth-title">
            {screen === 'login' && 'Log in'}
            {screen === 'register' && 'Register'}
            {screen === 'loginOtp' && 'Verify login'}
            {screen === 'forgotEmail' && 'Forgot password'}
            {screen === 'forgotOtp' && 'Verify OTP'}
            {screen === 'resetPassword' && 'New password'}
            {screen === 'adminLogin' && 'Admin Verification'}
          </h1>

          <div style={{ textAlign: 'center', marginBottom: '14px' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '11px',
                fontWeight: 600,
                padding: '3px 10px',
                borderRadius: '999px',
                background: 'rgba(59, 130, 246, 0.12)',
                color: '#3b82f6',
                border: '1px solid currentColor',
              }}
            >
              📧 Free Email OTP Verification Active
            </span>
          </div>

          {screen === 'login' && (
            <>
              <form onSubmit={handleLogin} className="auth-form">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                />

                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={1}
                  maxLength={128}
                  required
                  autoComplete="current-password"
                />

                <button type="submit" disabled={loading}>
                  {loading ? 'Logging in...' : 'Log in'}
                </button>
              </form>

              <div className="auth-links">
                <button type="button" className="text-button" onClick={() => goTo('forgotEmail')}>
                  Forgot password?
                </button>
                <button type="button" className="text-button" onClick={() => goTo('register')}>
                  Create an account
                </button>
              </div>

              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <button
                  type="button"
                  className="text-button"
                  style={{ color: '#8c9ba5', fontSize: '13px' }}
                  onClick={() => goTo('adminLogin')}
                >
                  🔒 Admin Portal
                </button>
              </div>
            </>
          )}

          {screen === 'adminLogin' && (
            <form onSubmit={handleAdminLogin} className="auth-form">
              <p className="form-copy">Enter the 6-digit passcode to access temporary admin controls.</p>
              <label htmlFor="adminPasscode">Admin Passcode</label>
              <input
                id="adminPasscode"
                type="password"
                value={adminPasscode}
                onChange={(event) => setAdminPasscode(event.target.value)}
                placeholder="Enter passcode"
                required
                autoComplete="off"
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Verifying...' : 'Unlock Admin Panel'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Back to login
              </button>
            </form>
          )}

          {screen === 'register' && (
            <form
              onSubmit={async (event) => {
                event.preventDefault()
                setLoading(true)
                setError('')
                setMessage('')
                try {
                  await apiRequest('/register', {
                    method: 'POST',
                    body: JSON.stringify({
                      full_name: fullName,
                      email,
                      phone,
                      password,
                    }),
                  })
                  setPassword('')
                  setFullName('')
                  setPhone('')
                  goTo('login')
                  setMessage('Account created successfully. Please log in.')
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Registration failed')
                } finally {
                  setLoading(false)
                }
              }}
              className="auth-form"
            >
              <label htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                minLength={2}
                maxLength={100}
                required
                autoComplete="name"
              />

              <label htmlFor="registerEmail">Email</label>
              <input
                id="registerEmail"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />

              <label htmlFor="phone">Phone</label>
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                minLength={10}
                maxLength={15}
                required
                autoComplete="tel"
              />

              <label htmlFor="registerPassword">Password</label>
              <input
                id="registerPassword"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={8}
                maxLength={128}
                required
                autoComplete="new-password"
              />
              <p className="password-hint">Use at least 8 characters.</p>

              <button type="submit" disabled={loading}>
                {loading ? 'Creating account...' : 'Register'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Back to login
              </button>
            </form>
          )}

          {screen === 'loginOtp' && (
            <form onSubmit={handleLoginOtp} className="auth-form">
              <p className="form-copy">
                Enter the six-digit verification code sent to {maskedEmail || maskedPhone || 'your registered email/phone'}.
              </p>
              <label htmlFor="loginOtp">Six-digit OTP</label>
              <input
                id="loginOtp"
                inputMode="numeric"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                minLength={6}
                maxLength={6}
                required
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Back to login
              </button>
            </form>
          )}

          {screen === 'forgotEmail' && (
            <form onSubmit={handleForgotEmail} className="auth-form">
              <p className="form-copy">
                Enter your registered email. An OTP will be sent to your registered phone number.
              </p>
              <label htmlFor="forgotEmail">Email</label>
              <input
                id="forgotEmail"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Generating...' : 'Generate OTP'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Back to login
              </button>
            </form>
          )}

          {screen === 'forgotOtp' && (
            <form onSubmit={handleForgotOtp} className="auth-form">
              <p className="form-copy">
                Enter the six-digit verification code sent to {maskedEmail || maskedPhone || 'your registered email/phone'}.
              </p>
              <label htmlFor="forgotOtp">Six-digit OTP</label>
              <input
                id="forgotOtp"
                inputMode="numeric"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                minLength={6}
                maxLength={6}
                required
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Back to login
              </button>
            </form>
          )}

          {screen === 'resetPassword' && (
            <form onSubmit={handleResetPassword} className="auth-form">
              <label htmlFor="newPassword">New password</label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={8}
                maxLength={128}
                required
                autoComplete="new-password"
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Resetting...' : 'Reset password'}
              </button>
              <button type="button" className="secondary-button" onClick={() => goTo('login')}>
                Cancel
              </button>
            </form>
          )}

          {error && <p className="status error" role="alert">{error}</p>}
          {message && <p className="status success" role="status">{message}</p>}
        </section>
      ) : screen === 'adminDashboard' ? (
        <section className="profile-card admin-view" aria-labelledby="admin-title">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h1 id="admin-title" style={{ margin: 0 }}>Admin Management</h1>
            <span className="badge-active">Authorized</span>
          </div>
          <p className="form-copy" style={{ marginTop: '8px' }}>
            Temporary user monitoring and block/unblock control panel.
          </p>

          <div className="admin-header">
            <h2>Registered Users ({adminUsers.length})</h2>
            <button
              type="button"
              className="text-button"
              onClick={loadAdminUsers}
              disabled={adminLoading}
            >
              {adminLoading ? 'Refreshing...' : '↻ Refresh list'}
            </button>
          </div>

          <div className="table-responsive">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {adminUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '16px' }}>
                      No users registered yet.
                    </td>
                  </tr>
                ) : (
                  adminUsers.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.full_name}</td>
                      <td>{u.email}</td>
                      <td>{u.phone}</td>
                      <td>
                        {!u.is_active ? (
                          <span className="badge-blocked">Blocked</span>
                        ) : u.is_logged_in ? (
                          <span className="badge-active">Active</span>
                        ) : (
                          <span className="badge-inactive">Inactive</span>
                        )}
                      </td>
                      <td>
                        {u.is_active ? (
                          <button
                            type="button"
                            className="btn-block"
                            onClick={() => handleToggleBlock(u.id)}
                          >
                            Block
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn-unblock"
                            onClick={() => handleToggleBlock(u.id)}
                          >
                            Unblock
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {error && <p className="status error" role="alert">{error}</p>}
          {message && <p className="status success" role="status">{message}</p>}

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              sessionStorage.removeItem('admin_token')
              setAdminPasscode('')
              setAdminUsers([])
              goTo('login')
            }}
          >
            Exit Admin Panel
          </button>
        </section>
      ) : (
        <section className="profile-card" aria-labelledby="profile-title">
          <h1 id="profile-title">Profile</h1>
          {profile && (
            <dl>
              <div>
                <dt>Full name</dt>
                <dd>{profile.full_name}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{profile.email}</dd>
              </div>
              <div>
                <dt>Phone</dt>
                <dd>{profile.phone}</dd>
              </div>
            </dl>
          )}

          {error && <p className="status error" role="alert">{error}</p>}
          {message && <p className="status success" role="status">{message}</p>}

          <button type="button" onClick={handleLogout}>Log out</button>
        </section>
      )}
    </main>
  )
}

export default App
