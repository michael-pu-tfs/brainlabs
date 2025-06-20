// import { Navigate, useNavigate, useLocation } from 'react-router-dom'
// import { useEffect } from 'react'
// import { API_BASE_URL } from '@/config'
// interface ProtectedRouteProps {
//   children: React.ReactNode
// }

// export function ProtectedRoute({ children }: ProtectedRouteProps) {
//   const navigate = useNavigate()
//   const location = useLocation()
  
//   useEffect(() => {
//     // Check if we're already on the login page to prevent redirect loops
//     if (location.pathname === '/login') {
//       return
//     }

//     const checkAuth = async () => {
//       try {
//         const response = await fetch(`${API_BASE_URL}/api/auth/verify`, {
//           credentials: 'include',
//           headers: { "Content-Type": "application/json" },
//         })

//         if (!response.ok) {
//           localStorage.removeItem("isAuthenticated")
//           navigate('/login')
//         }
//       } catch (error) {
//         localStorage.removeItem("isAuthenticated")
//         navigate('/login')
//       }
//     }

//     checkAuth()
//   }, [navigate, location])

//   const isAuthenticated = localStorage.getItem("isAuthenticated") === "true"

//   if (!isAuthenticated) {
//     return <Navigate to="/login" replace />
//   }

//   return <>{children}</>
// } 





import { Navigate, useLocation } from 'react-router-dom'
// import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()

  // Check if we're already on the login page to prevent redirect loops
  if (location.pathname === '/login') {
    return <>{children}</>
  }

  const isAuthenticated = localStorage.getItem("isAuthenticated") === "true"

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
