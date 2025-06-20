// import { cn } from "@/lib/utils"
// import { Button } from "@/components/ui/button"
// import {
//   Card,
//   CardContent,
//   CardDescription,
//   CardHeader,
//   CardTitle,
// } from "@/components/ui/card"
// import { Input } from "@/components/ui/input"
// import { Label } from "@/components/ui/label"
// import { useState } from "react"
// import { useNavigate } from "react-router-dom"
// import { useGoogleLogin } from '@react-oauth/google'
// import { API_BASE_URL } from '@/config'

// export function LoginForm({
//   className,
//   ...props
// }: React.ComponentPropsWithoutRef<"div">) {
//   const navigate = useNavigate()
//   const [email, setEmail] = useState("")
//   const [password, setPassword] = useState("")
//   const [error, setError] = useState("")

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault()
//     setError("")
    
//     try {
//       const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/x-www-form-urlencoded',
//         },
//         body: new URLSearchParams({
//           username: email,
//           password: password,
//         }),
//         credentials: 'include',
//       })

//       if (response.ok) {
//         const data = await response.json()
//         localStorage.setItem("isAuthenticated", "true")
//         localStorage.setItem("userName", data.name)
//         setPassword("")
//         setEmail("")
        
//         const verifyResponse = await fetch(`${API_BASE_URL}/api/auth/verify`, {
//           credentials: 'include',
//           headers: { "Content-Type": "application/json" },
//         })

//         if (verifyResponse.ok) {
//           navigate('/')
//         } else {
//           throw new Error('Verification failed')
//         }
//       } else {
//         throw new Error('Login failed')
//       }
//     } catch (error) {
//       setError("Invalid email or password")
//       console.error("Authentication failed")
//     }
//   }

//   const googleLogin = useGoogleLogin({
//     onSuccess: async (response) => {
//       try {
//         const result = await fetch(`${API_BASE_URL}/api/auth/google`, {
//           method: 'POST',
//           headers: {
//             'Content-Type': 'application/json',
//           },
//           body: JSON.stringify({ token: response.access_token }),
//           credentials: 'include',
//         })

//         const data = await result.json()

//         if (!result.ok) {
//           throw new Error(data.detail || 'Google login failed')
//         }

//         localStorage.setItem("isAuthenticated", "true")
//         localStorage.setItem("userName", data.name)
//         navigate('/')
//       } catch (error) {
//         setError("Google login failed")
//         console.error("Google login error:", error)
//       }
//     },
//   })

//   return (
//     <div className={cn("grid gap-6", className)} {...props}>
//       <Card>
//         <CardHeader className="space-y-1">
//           <CardTitle className="text-2xl font-bold">Login</CardTitle>
//           <CardDescription>
//             Enter your email and password to login to your account
//           </CardDescription>
//         </CardHeader>
//         <CardContent>
//           {error && (
//             <div className="mb-4 text-sm text-red-500">
//               {error}
//             </div>
//           )}
//           <form onSubmit={handleSubmit}>
//             <div className="grid gap-4">
//               <div className="grid gap-2">
//                 <Label htmlFor="email">Email</Label>
//                 <Input
//                   id="email"
//                   type="email"
//                   placeholder="m@example.com"
//                   value={email}
//                   onChange={(e) => setEmail(e.target.value)}
//                   required
//                 />
//               </div>
//               <div className="grid gap-2">
//                 <div className="flex items-center justify-between">
//                   <Label htmlFor="password">Password</Label>
//                   <Button variant="link" className="px-0 font-normal">
//                     Forgot password?
//                   </Button>
//                 </div>
//                 <Input
//                   id="password"
//                   type="password"
//                   value={password}
//                   onChange={(e) => setPassword(e.target.value)}
//                   required
//                 />
//               </div>
//               <Button className="w-full" type="submit">
//                 Sign in
//               </Button>
//             </div>
//           </form>
//           <div className="relative my-4">
//             <div className="absolute inset-0 flex items-center">
//               <span className="w-full border-t" />
//             </div>
//             <div className="relative flex justify-center text-xs uppercase">
//               <span className="bg-background px-2 text-muted-foreground">
//                 Or continue with
//               </span>
//             </div>
//           </div>
//           <Button 
//             variant="outline" 
//             className="w-full"
//             onClick={() => googleLogin()}
//           >
//             Login with Google
//           </Button>
//           <p className="mt-4 text-center text-sm text-muted-foreground">
//             Don't have an account?{" "}
//             <Button variant="link" className="px-0" onClick={() => navigate('/register')}>
//               Sign up
//             </Button>
//           </p>
//         </CardContent>
//       </Card>
//     </div>
//   )
// }








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
import { API_BASE_URL } from '@/config'

export function LoginForm({
  className,
  ...props
}: React.ComponentPropsWithoutRef<"div">) {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
        credentials: 'include',
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem("isAuthenticated", "true")
        localStorage.setItem("userName", data.name)
        setPassword("")
        setEmail("")
        navigate('/')
      } else {
        throw new Error('Login failed')
      }
    } catch (error) {
      setError("Invalid email or password")
      console.error("Authentication failed")
    }
  }

  const googleLogin = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const result = await fetch(`${API_BASE_URL}/api/auth/google`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: response.access_token }),
          credentials: 'include',
        })

        const data = await result.json()

        if (!result.ok) {
          throw new Error(data.detail || 'Google login failed')
        }

        localStorage.setItem("isAuthenticated", "true")
        localStorage.setItem("userName", data.name)
        navigate('/')
      } catch (error) {
        setError("Google login failed")
        console.error("Google login error:", error)
      }
    },
  })

  return (
    <div className={cn("grid gap-6", className)} {...props}>
      <Card>
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Login</CardTitle>
          <CardDescription>
            Enter your email and password to login to your account
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
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Button variant="link" className="px-0 font-normal">
                    Forgot password?
                  </Button>
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button className="w-full" type="submit">
                Sign in
              </Button>
            </div>
          </form>
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => googleLogin()}
          >
            Login with Google
          </Button>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Button variant="link" className="px-0" onClick={() => navigate('/register')}>
              Sign up
            </Button>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
