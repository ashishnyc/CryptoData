import { colors } from '../theme/colors';
import { useTheme } from '../contexts/ThemeContext';

export const useThemeColors = () => {
    const { isDark } = useTheme();

    const getColor = (path) => {
        const pathArray = path.split('.');
        let result = colors;

        for (const key of pathArray) {
            result = result[key];
        }

        return result[isDark ? 'dark' : 'light'];
    };

    return { getColor };
};