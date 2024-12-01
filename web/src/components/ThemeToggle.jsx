import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useThemeColors } from '../hooks/useThemeColors';

const ThemeToggle = () => {
    const { getColor } = useThemeColors();
    const { isDark, toggleTheme } = useTheme();

    const handleToggle = () => {
        console.log('Current theme:', isDark ? 'dark' : 'light');
        toggleTheme();
        console.log('Theme after toggle:', !isDark ? 'dark' : 'light');
    };

    return (
        <button
            onClick={handleToggle}
            className={`
                flex items-center justify-center 
                rounded-lg 
                transition-colors
                border 
                ${getColor('border.primary')}
                ${getColor('hover.background')}
                ${getColor('background.secondary')}
            `}
        >
            {isDark ? (
                <Sun className={`w-5 h-5 ${getColor('icon.light')}`} />
            ) : (
                <Moon className={`w-5 h-5 ${getColor('icon.dark')}`} />
            )}
        </button>
    );
};

export default ThemeToggle;
