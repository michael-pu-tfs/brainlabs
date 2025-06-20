import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useGoogleLogin } from '@react-oauth/google'
// import { log } from "console"
import { API_BASE_URL } from '@/config'

export function RegisterForm({
  className,
  ...props
}: React.ComponentPropsWithoutRef<"div">) {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
    confirmPassword: ""
  })
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match")
      return
    }

    const registrationData = {
      email: formData.email,
      password: formData.password,
      name: formData.name
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(registrationData),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      setFormData({
        email: "",
        password: "",
        name: "",
        confirmPassword: ""
      })

      navigate('/login')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Registration failed')
      console.error("Registration error occurred")
    }
  }

  const googleRegister = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const result = await fetch(`${API_BASE_URL}/api/auth/register/google`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: response.access_token }),
        })

        const data = await result.json()
        console.log("Google registration response:", data)

        if (!result.ok) {
          throw new Error(data.detail || 'Google registration failed')
        }

        // Registration successful
        navigate('/login')
      } catch (error) {
        console.error("Google registration error:", error)
        setError(error instanceof Error ? error.message : 'Google registration failed')
      }
    },
  })

  return (
    <div className={cn("grid gap-6", className)} {...props}>
      <Card>
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
          <CardDescription>
            Enter your details below to create your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 text-sm text-red-500">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  minLength={8}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  minLength={8}
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                  required
                />
              </div>
              <Button className="w-full" type="submit">
                Create account
              </Button>
            </div>
          </form>
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or register with
              </span>
            </div>
          </div>
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => googleRegister()}
          >
            Register with Google
          </Button>
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Button variant="link" className="px-0" onClick={() => navigate('/login')}>
              Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 