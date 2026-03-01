import { useState } from 'react';

const navItems = [
    { id: 'library', label: 'Library', icon: 'auto_stories' },
    { id: 'chatbot', label: 'Chatbot (RAG)', icon: 'smart_toy' },
    { id: 'viewer', label: 'Drawing Viewer', icon: 'engineering' },
];

export default function Sidebar({ active, onNavigate, collapsed, onToggle }) {
    return (
        <aside
            className={`${collapsed ? 'w-16' : 'w-56'
                } bg-surface-dark border-r border-gray-800 flex flex-col transition-all duration-300 h-screen`}
        >
            {/* Brand */}
            <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                    Ai
                </div>
                {!collapsed && (
                    <div>
                        <div className="font-bold text-white text-sm">DOCS.ai</div>
                        <div className="text-[10px] text-gray-500">TNB Genco</div>
                    </div>
                )}
                <button
                    onClick={onToggle}
                    className="ml-auto text-gray-500 hover:text-white transition-colors"
                >
                    <span className="material-symbols-outlined text-lg">
                        {collapsed ? 'chevron_right' : 'chevron_left'}
                    </span>
                </button>
            </div>

            {/* Nav Links */}
            <nav className="flex-1 py-3 px-2 space-y-1">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active === item.id
                                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                : 'text-slate-400 hover:bg-slate-800/50 border border-transparent'
                            }`}
                    >
                        <span className="material-symbols-outlined text-xl">{item.icon}</span>
                        {!collapsed && item.label}
                    </button>
                ))}
            </nav>

            {/* User */}
            <div className="px-3 py-4 border-t border-gray-800">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                        EU
                    </div>
                    {!collapsed && (
                        <div>
                            <div className="text-sm font-medium text-white">Engineer User</div>
                            <div className="text-xs text-gray-500">Settings</div>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}
