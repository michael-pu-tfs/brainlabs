import { RegisterForm } from "@/components/register-form"
import { Logo } from "@/components/Logo"

export default function RegisterPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <RegisterForm />
      </div>
    </div>
  )
} 