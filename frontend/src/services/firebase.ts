import { initializeApp, getApps, type FirebaseApp } from 'firebase/app'
import {
  getAuth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  type Auth,
  type ConfirmationResult,
} from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyDTn53BPiAyud3nFKDtThMLTcDTIsQp69M',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'login-setup-15c40.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'login-setup-15c40',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'login-setup-15c40.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '174080716582',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:174080716582:web:dcb77d0c37ace918d25be7',
}

export function isFirebaseConfigured(): boolean {
  return Boolean(
    firebaseConfig.apiKey &&
      firebaseConfig.apiKey.trim() !== '' &&
      firebaseConfig.projectId &&
      firebaseConfig.projectId.trim() !== ''
  )
}

let app: FirebaseApp | null = null
let auth: Auth | null = null
let recaptchaVerifier: RecaptchaVerifier | null = null

function getFirebaseAuth(): Auth {
  if (!auth) {
    app = getApps().length > 0 ? getApps()[0] : initializeApp(firebaseConfig)
    auth = getAuth(app)
  }
  return auth
}

export function setupRecaptcha(containerId: string): RecaptchaVerifier {
  const authInstance = getFirebaseAuth()
  if (recaptchaVerifier) {
    try {
      recaptchaVerifier.clear()
    } catch {
      // Ignore if already cleared
    }
    recaptchaVerifier = null
  }

  recaptchaVerifier = new RecaptchaVerifier(authInstance, containerId, {
    size: 'invisible',
    callback: () => {
      // reCAPTCHA solved
    },
    'expired-callback': () => {
      // Response expired
    },
  })

  return recaptchaVerifier
}

export function formatE164Phone(phone: string): string {
  const cleaned = phone.replace(/[^0-9+]/g, '')
  if (cleaned.startsWith('+')) {
    return cleaned
  }
  // Default to +91 (India) if 10 digits provided, or add leading '+'
  if (cleaned.length === 10) {
    return `+91${cleaned}`
  }
  return `+${cleaned}`
}

export async function sendFirebaseOtp(
  phoneNumber: string,
  containerId: string = 'recaptcha-container'
): Promise<ConfirmationResult> {
  const authInstance = getFirebaseAuth()
  const verifier = setupRecaptcha(containerId)
  const e164Phone = formatE164Phone(phoneNumber)
  return await signInWithPhoneNumber(authInstance, e164Phone, verifier)
}

export async function verifyFirebaseOtpCode(
  confirmationResult: ConfirmationResult,
  otpCode: string
): Promise<string> {
  const result = await confirmationResult.confirm(otpCode)
  const idToken = await result.user.getIdToken()
  return idToken
}
