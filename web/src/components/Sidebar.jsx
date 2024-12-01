import React, { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useThemeColors } from '../hooks/useThemeColors';
import { House, ChartCandlestick, CalendarClock, Radio, Bitcoin, SquareUserRound } from 'lucide-react';

const Sidebar = () => {
    const { getColor } = useThemeColors();
    const location = useLocation();

    const menuItems = useMemo(() => [
        {
            id: 'home',
            path: '/',
            icon: <House className="w-6 h-6 stroke-current" />
        },
        {
            id: 'markets',
            path: '/markets',
            icon: <ChartCandlestick className="w-6 h-6 stroke-current" />
        },
        {
            id: 'backtest',
            path: '/backtest',
            icon: <CalendarClock className="w-6 h-6 stroke-current" />
        },
        {
            id: 'live',
            path: '/live',
            icon: <Radio className="w-6 h-6 stroke-current" />
        }
    ], []);

    const isPathActive = (path) => {
        if (path === '/') {
            return location.pathname === '/';
        }
        return location.pathname === path;
    };

    return (
        <div className={`w-16 border-r ${getColor('background.primary')} ${getColor('border.primary')}`}>
            <div className={`flex flex-col items-center h-full ${getColor('text.tertiary')} rounded`}>
                <Link to="/" className="flex items-center justify-center mt-3">
                    <Bitcoin className="w-10 h-10 stroke-current text-yellow-500" />
                </Link>

                <div className={`flex flex-col items-center mt-3 border-t ${getColor('border.primary')}`}>
                    {menuItems.map((item) => {
                        const isActive = isPathActive(item.path);
                        console.log(isActive, item.path);
                        return (
                            <Link
                                key={item.id}
                                to={item.path}
                                className={`
                                flex items-center justify-center w-12 h-12 mt-2 rounded
                                ${getColor('hover.background')}
                                ${isActive ? getColor('background.secondary') : ''}
                            `}
                            >
                                {item.icon}
                            </Link>
                        );
                    }
                    )}
                </div>
                <Link
                    to="/profile"
                    className={`flex items-center justify-center w-12 h-12 mt-auto rounded 
                  ${getColor('hover.background')}
                  ${isPathActive('/profile') ? getColor('background.secondary') : ''}`}
                >
                    <SquareUserRound className="w-6 h-6 stroke-current" />
                </Link>
            </div>
        </div>
    );
};

export default Sidebar;