import { useState } from 'react'
import { Button } from './ui/button'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'
import { useTheme } from '../contexts/ThemeContext'
import { 
  Sun, 
  Moon, 
  Monitor,
  Palette,
  Check
} from 'lucide-react'

export function ThemeToggle() {
  const { theme, toggleTheme, setLightTheme, setDarkTheme, setSystemTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="w-9 px-0">
          {theme === 'light' ? (
            <Sun className="h-4 w-4" />
          ) : theme === 'dark' ? (
            <Moon className="h-4 w-4" />
          ) : (
            <Monitor className="h-4 w-4" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem 
          onClick={setLightTheme}
          className="cursor-pointer"
        >
          <Sun className="mr-2 h-4 w-4" />
          <span>Light</span>
          {theme === 'light' && <Check className="ml-auto h-4 w-4" />}
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={setDarkTheme}
          className="cursor-pointer"
        >
          <Moon className="mr-2 h-4 w-4" />
          <span>Dark</span>
          {theme === 'dark' && <Check className="ml-auto h-4 w-4" />}
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={setSystemTheme}
          className="cursor-pointer"
        >
          <Monitor className="mr-2 h-4 w-4" />
          <span>System</span>
          {theme === 'system' && <Check className="ml-auto h-4 w-4" />}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <Button 
      variant="outline" 
      size="sm" 
      onClick={toggleTheme}
      className="flex items-center gap-2"
    >
      {theme === 'light' ? (
        <>
          <Moon className="h-4 w-4" />
          <span className="hidden sm:inline">Dark Mode</span>
        </>
      ) : (
        <>
          <Sun className="h-4 w-4" />
          <span className="hidden sm:inline">Light Mode</span>
        </>
      )}
    </Button>
  )
}