import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import LibraryPage from './pages/LibraryPage';
import ChatbotPage from './pages/ChatbotPage';
import ViewerPage from './pages/ViewerPage';
import { healthCheck } from './api';

export default function App() {
    const [activePage, setActivePage] = useState('library');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [viewerDoc, setViewerDoc] = useState(null);
    const [apiStatus, setApiStatus] = useState(null);

    useEffect(() => {
        healthCheck()
            .then((r) => setApiStatus(r.data))
            .catch(() => setApiStatus({ status: 'offline' }));
    }, []);

    const openInViewer = (doc) => {
        setViewerDoc(doc);
        setActivePage('viewer');
    };

    return (
        <div className="flex h-screen bg-bg-dark overflow-hidden">
            {/* Sidebar */}
            <Sidebar
                active={activePage}
                onNavigate={setActivePage}
                collapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Main Content */}
            <main className="flex-1 overflow-hidden">
                {activePage === 'library' && (
                    <LibraryPage onOpenViewer={openInViewer} />
                )}
                {activePage === 'chatbot' && (
                    <ChatbotPage onOpenViewer={openInViewer} />
                )}
                {activePage === 'viewer' && (
                    <ViewerPage document={viewerDoc} />
                )}
            </main>
        </div>
    );
}
