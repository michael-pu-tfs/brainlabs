import { User, Moon, Sun, LogOut } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { useNavigate } from "react-router-dom"
import { Logo } from "./Logo"
import { useEffect, useState } from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { API_BASE_URL } from '@/config'
interface NavbarProps {
  theme: string;
  toggleTheme: () => void;
}

export function Navbar({ theme, toggleTheme }: NavbarProps) {
  const navigate = useNavigate()
  const [userName, setUserName] = useState<string>("")

  useEffect(() => {
    // Get user info from localStorage or fetch from backend
    const storedUserName = localStorage.getItem("userName")
    if (storedUserName) {
      setUserName(storedUserName)
    }
  }, [])

  const handleLogout = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })

      if (response.ok) {
        localStorage.removeItem("isAuthenticated")
        localStorage.removeItem("token")
        localStorage.removeItem("userName") // Also remove userName
        navigate("/login")
      } else {
        console.error("Logout failed")
      }
    } catch (error) {
      console.error("Logout error:", error)
    }
  }

  return (
    <nav className="bg-background shadow-md p-4 w-full fixed top-0 left-0 z-50">
      <div className="flex justify-between items-center max-w-[2000px] mx-auto">
        <Logo />
        
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={toggleTheme}>
            {theme === "dark" ? <Sun className="h-[1.2rem] w-[1.2rem]" /> : <Moon className="h-[1.2rem] w-[1.2rem]" />}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <User size={20} />
                <span>{userName || "Account"}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
              <DropdownMenuLabel>
                {userName ? `Signed in as ${userName}` : "My Account"}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate("/profile")}>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                className="text-red-600 focus:text-red-600" 
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  )
}
