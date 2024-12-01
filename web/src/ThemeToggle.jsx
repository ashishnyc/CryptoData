// ThemeToggle.jsx
import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from './contexts/ThemeContext';

const ThemeToggle = () => {
    const { isDark, setIsDark } = useTheme();

    return (
        <button
            onClick={() => setIsDark(!isDark)}
            className={`
                flex items-center justify-center 
                rounded-lg 
                transition-colors
                ${isDark
                    ? 'bg-[#1C2127] border border-gray-800 hover:bg-[#2D3748]'
                    : 'bg-white border border-gray-200 hover:bg-gray-100'
                }
            `}
            aria-label="Toggle theme"
        >
            {isDark ? (
                <Sun className="w-5 h-5 text-gray-400" />
            ) : (
                <Moon className="w-5 h-5 text-gray-600" />
            )}
        </button>
    );
};

export default ThemeToggle;