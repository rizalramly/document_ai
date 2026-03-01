import { useState, useEffect } from 'react';
import { getAnnotations, createAnnotation, getPageRenderUrl, getPdfUrl } from '../api';

export default function ViewerPage({ document: doc }) {
    const [currentPage, setCurrentPage] = useState(1);
    const [zoom, setZoom] = useState(75);
    const [layers, setLayers] = useState({ base: true, electrical: true, fluid: false });
    const [annotations, setAnnotations] = useState([]);
    const [chatMessages, setChatMessages] = useState([
        {
            role: 'assistant',
            content: doc
                ? `I'm analyzing the <strong>${doc.original_filename}</strong>. I can help you locate components, explain the flow, or identify potential failure points.`
                : "Open a document from the Library to start viewing.",
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
    ]);
    const [chatInput, setChatInput] = useState('');
    const totalPages = doc?.page_count || 14;

    useEffect(() => {
        if (doc?.id) {
            getAnnotations(doc.id).then((r) => setAnnotations(r.data)).catch(() => { });
        }
    }, [doc?.id]);

    const handleAddAnnotation = async (severity) => {
        if (!doc) return;
        const text = prompt(`Enter ${severity} annotation text:`);
        if (!text) return;
        try {
            const res = await createAnnotation({
                document_id: doc.id,
                page_number: currentPage,
                severity,
                text,
                author: 'Engineer User',
            });
            setAnnotations((prev) => [res.data, ...prev]);
        } catch (err) {
            alert('Failed to create annotation');
        }
    };

    const severityColors = {
        warning: { bg: 'border-l-yellow-500', text: 'text-yellow-500' },
        note: { bg: 'border-l-blue-500', text: 'text-blue-500' },
        critical: { bg: 'border-l-red-500', text: 'text-red-500' },
    };

    return (
        <div className="flex h-full">
            {/* Left Panel - Document Info */}
            <div className="w-72 border-r border-gray-800 bg-surface-dark flex flex-col overflow-y-auto">
                <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-blue-400">engineering</span>
                        <h3 className="font-semibold text-white text-sm">DOCS.ai Viewer</h3>
                    </div>
                    <button className="text-gray-500 hover:text-white">
                        <span className="material-symbols-outlined text-lg">tune</span>
                    </button>
                </div>

                {/* Document info */}
                <div className="px-4 py-3 border-b border-gray-700">
                    <p className="font-medium text-white text-sm">{doc?.original_filename || 'P&ID - Turbine System 04'}</p>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs bg-blue-900 text-blue-200 px-2 py-0.5 rounded font-medium">REV 3.2</span>
                        <span className="text-xs text-gray-500">Last mod: 2h ago</span>
                    </div>
                </div>

                {/* Layers */}
                <div className="px-4 py-3 border-b border-gray-700">
                    <h4 className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Layers</h4>
                    {Object.entries({ base: 'Base Schematic', electrical: 'Electrical Overlay', fluid: 'Fluid Dynamics' }).map(([key, label]) => (
                        <label key={key} className="flex items-center gap-2 py-1 cursor-pointer">
                            <input type="checkbox" checked={layers[key]}
                                onChange={() => setLayers({ ...layers, [key]: !layers[key] })}
                                className="rounded border-gray-600" />
                            <span className={`text-sm ${layers[key] ? 'text-white' : 'text-gray-500'}`}>{label}</span>
                        </label>
                    ))}
                </div>

                {/* Annotations */}
                <div className="px-4 py-3 flex-1">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs text-gray-500 font-semibold uppercase tracking-wide">
                            Annotations <span className="bg-gray-700 px-1.5 py-0.5 rounded-full text-xs">{annotations.length}</span>
                        </h4>
                        <div className="flex gap-1">
                            <button onClick={() => handleAddAnnotation('warning')}
                                className="text-yellow-500 hover:text-yellow-400 text-xs">+ Warning</button>
                            <button onClick={() => handleAddAnnotation('critical')}
                                className="text-red-500 hover:text-red-400 text-xs">+ Critical</button>
                        </div>
                    </div>
                    <div className="space-y-2">
                        {annotations.length > 0 ? annotations.map((a) => {
                            const sc = severityColors[a.severity] || severityColors.note;
                            return (
                                <div key={a.id} className={`bg-gray-800/50 rounded-lg p-2.5 border-l-2 ${sc.bg}`}>
                                    <div className="flex justify-between items-start">
                                        <span className={`text-xs font-medium capitalize ${sc.text}`}>{a.severity}</span>
                                        <span className="text-xs text-gray-600">{new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    </div>
                                    <p className="text-sm text-gray-300 mt-1">{a.text}</p>
                                    <p className="text-xs text-gray-600 mt-0.5">👤 {a.author || 'Unknown'}</p>
                                </div>
                            );
                        }) : (
                            <p className="text-xs text-gray-600 text-center py-4">No annotations yet</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Center - Canvas */}
            <div className="flex-1 flex flex-col bg-bg-dark">
                {/* Breadcrumb */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <span>← Library</span>
                        <span>/</span>
                        <span className="text-white">{doc?.cluster || 'Boiler System'}</span>
                        <span>/</span>
                        <span className="text-white">{doc?.original_filename || 'Document.pdf'}</span>
                    </div>
                    <button className="w-8 h-8 rounded-lg bg-red-500/20 hover:bg-red-500/30 flex items-center justify-center">
                        <span className="material-symbols-outlined text-red-400">close</span>
                    </button>
                </div>

                {/* Toolbar */}
                <div className="absolute left-80 top-24 z-10 flex flex-col gap-1 bg-surface-dark border border-gray-700 rounded-lg p-1">
                    {['near_me', 'edit', 'gesture', 'format_paint', 'title', 'grid_view', 'note_add', 'delete'].map((icon) => (
                        <button key={icon} className="w-8 h-8 rounded hover:bg-gray-700 flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                            <span className="material-symbols-outlined text-lg">{icon}</span>
                        </button>
                    ))}
                </div>

                {/* Canvas area */}
                <div className="flex-1 overflow-auto grid-bg flex items-center justify-center p-8">
                    {doc?.id ? (
                        <img
                            src={getPageRenderUrl(doc.id, currentPage)}
                            alt={`Page ${currentPage}`}
                            className="max-w-full max-h-full border border-gray-700 rounded-lg shadow-2xl"
                            style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center' }}
                            onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.parentElement.innerHTML = '<div class="text-gray-500 text-center"><span class="material-symbols-outlined text-6xl mb-2 block">image_not_supported</span><p>Page render not available</p></div>';
                            }}
                        />
                    ) : (
                        <div className="text-gray-600 text-center">
                            <span className="material-symbols-outlined text-8xl mb-4 block">draw</span>
                            <p className="text-lg">Select a document from the Library to view</p>
                        </div>
                    )}
                </div>

                {/* Bottom Bar */}
                <div className="flex items-center justify-center gap-4 px-4 py-2 border-t border-gray-800 bg-surface-dark">
                    <span className="text-sm text-gray-400">Page</span>
                    <button onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">remove</span>
                    </button>
                    <span className="text-sm text-white font-medium">{currentPage}/{totalPages}</span>
                    <button onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">add</span>
                    </button>

                    <input type="range" min="25" max="200" value={zoom}
                        onChange={(e) => setZoom(Number(e.target.value))}
                        className="w-32 accent-blue-500" />
                    <span className="text-sm text-white">{zoom}%</span>

                    <button className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">rotate_right</span>
                    </button>
                    <button className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">refresh</span>
                    </button>
                    <button className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined">fit_screen</span>
                    </button>
                </div>
            </div>

            {/* Right Panel - DOCS Assistant Chat */}
            <div className="w-80 border-l border-gray-800 bg-surface-dark flex flex-col">
                <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-green-400">smart_toy</span>
                        <h3 className="font-semibold text-white text-sm">DOCS Assistant</h3>
                        <span className="flex items-center gap-1 text-xs text-green-400">● Online</span>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
                    {chatMessages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'items-start gap-2'}`}>
                            {msg.role === 'assistant' && (
                                <div className="w-6 h-6 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0 mt-1">
                                    <span className="text-white text-[10px] font-bold">Ai</span>
                                </div>
                            )}
                            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-gray-800/80 text-gray-300 rounded-tl-none'
                                }`}>
                                <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                                <p className="text-[10px] text-gray-500 mt-1">{msg.time}</p>
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 mt-1">
                                    <span className="text-white text-[10px] font-bold">EU</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="px-3 py-3 border-t border-gray-700">
                    <div className="flex items-center gap-2">
                        <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && chatInput.trim()) {
                                    setChatMessages((prev) => [...prev, {
                                        role: 'user', content: chatInput,
                                        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                                    }]);
                                    setChatInput('');
                                }
                            }}
                            placeholder="Ask about this drawing..."
                            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500" />
                        <button className="w-7 h-7 rounded-lg bg-green-600 hover:bg-green-700 flex items-center justify-center">
                            <span className="material-symbols-outlined text-white text-sm">send</span>
                        </button>
                    </div>
                    <div className="flex items-center gap-2 mt-1.5 text-[10px] text-gray-600">
                        <span className="material-symbols-outlined text-xs">attach_file</span>
                        Attach ref
                        <span className="ml-auto">AI can make mistakes. Verify critical info.</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
