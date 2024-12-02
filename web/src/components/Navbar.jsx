import { Search } from 'lucide-react';
import { useThemeColors } from '../hooks/useThemeColors';
import ThemeToggle from './ThemeToggle';

const Navbar = () => {
    const { getColor } = useThemeColors();

    return (
        <div className={`h-16 border-b flex items-center justify-between px-4 ${getColor('background.primary')} ${getColor('border.primary')}`}>
            <form className="flex-1 max-w-3xl mx-auto px-4">
                <div className="relative">
                    <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${getColor('text.secondary')}`} />
                    <input
                        type="text"
                        placeholder="Search..."
                        className={` w-full pl-10 pr-4 py-2.5 rounded-lg ${getColor('background.secondary')} placeholder:text-gray-500`}
                    />
                </div>
            </form>
            <ThemeToggle />
        </div>
    );
};

export default Navbar;