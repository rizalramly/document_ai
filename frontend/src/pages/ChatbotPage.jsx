import { useState, useRef, useEffect } from 'react';
import { chatQuery, getPageRenderUrl } from '../api';

export default function ChatbotPage({ onOpenViewer }) {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hello! I'm your Engineering Assistant. I have access to the full repository of RCA documents, P&IDs, and manuals for the Sultan Azlan Shah (Jimah) station. How can I help you today?",
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [sourceContext, setSourceContext] = useState(null);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || loading) return;
        const query = input.trim();
        setInput('');
        setMessages((prev) => [...prev, { role: 'user', content: query }]);
        setLoading(true);

        try {
            const res = await chatQuery({ query, session_id: sessionId });
            const data = res.data;
            setSessionId(data.session_id);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: data.answer,
                    citations: data.citations,
                    viewer_actions: data.viewer_actions,
                },
            ]);
            // Update source context with first citation
            if (data.citations?.length > 0) {
                const cite = data.citations[0];
                setSourceContext({
                    filename: cite.filename,
                    docId: cite.document_id,
                    pageNumber: cite.page_number,
                    relevanceScore: cite.relevance_score,
                    snippet: cite.snippet,
                });
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: 'Sorry, I encountered an error processing your request. Please try again.' },
            ]);
        }
        setLoading(false);
    };

    return (
        <div className="flex h-full">
            {/* Chat Area */}
            <div className="flex-1 flex flex-col">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                    {/* Timestamp */}
                    <div className="text-center">
                        <span className="text-xs text-gray-500 bg-surface-dark px-3 py-1 rounded-full">
                            Today, {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>

                    {messages.map((msg, i) => (
                        <MessageBubble key={i} message={msg} onOpenViewer={onOpenViewer} />
                    ))}

                    {loading && (
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                                <span className="text-white text-xs font-bold">Ai</span>
                            </div>
                            <div className="bg-surface-dark border border-gray-700 rounded-2xl rounded-tl-none px-4 py-3">
                                <div className="flex gap-1">
                                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Input */}
                <div className="px-6 py-4 border-t border-gray-800">
                    <div className="flex items-center gap-2 bg-surface-dark border border-gray-700 rounded-xl px-4 py-2">
                        <span className="material-symbols-outlined text-blue-400">auto_awesome</span>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Ask about engineering specs, drawings, or manuals..."
                            className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
                        />
                        <button onClick={sendMessage} disabled={loading || !input.trim()}
                            className="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 flex items-center justify-center disabled:opacity-50 transition-colors">
                            <span className="material-symbols-outlined text-white text-lg">send</span>
                        </button>
                    </div>
                    <p className="text-center text-xs text-gray-600 mt-2">
                        AI can make mistakes. Verify critical engineering data against original documents.
                    </p>
                </div>
            </div>

            {/* Source Context Panel */}
            <div className="w-96 border-l border-gray-800 bg-surface-dark flex flex-col">
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-blue-400">article</span>
                        Source Context
                    </h3>
                    <div className="flex items-center gap-1">
                        <button className="p-1 hover:bg-gray-700 rounded"><span className="material-symbols-outlined text-gray-400 text-lg">open_in_full</span></button>
                        <button className="p-1 hover:bg-gray-700 rounded"><span className="material-symbols-outlined text-gray-400 text-lg">close</span></button>
                    </div>
                </div>

                {sourceContext ? (
                    <div className="flex-1 overflow-y-auto">
                        {/* Document preview header */}
                        <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                            <span className="text-sm text-gray-300 truncate">{sourceContext.filename}</span>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                                Page {sourceContext.pageNumber || 1}
                                <button className="p-0.5 hover:bg-gray-700 rounded"><span className="material-symbols-outlined text-sm">remove</span></button>
                                <button className="p-0.5 hover:bg-gray-700 rounded"><span className="material-symbols-outlined text-sm">add</span></button>
                            </div>
                        </div>

                        {/* Page render preview */}
                        <div className="p-4">
                            {sourceContext.docId && sourceContext.pageNumber && (
                                <img
                                    src={getPageRenderUrl(sourceContext.docId, sourceContext.pageNumber)}
                                    alt="Page preview"
                                    className="w-full rounded-lg border border-gray-700"
                                    onError={(e) => { e.target.style.display = 'none'; }}
                                />
                            )}
                            <div className="mt-4 bg-gray-800/50 rounded-lg p-3 text-xs text-gray-400">
                                <p className="font-medium text-gray-300 mb-1">Snippet:</p>
                                <p>{sourceContext.snippet}</p>
                            </div>
                        </div>

                        {/* Metadata */}
                        <div className="px-4 pb-4 space-y-3">
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Document Metadata</h4>
                            <MetaRow label="File Name" value={sourceContext.filename} />
                            <MetaRow label="Page" value={sourceContext.pageNumber || 'N/A'} />
                            <MetaRow label="Relevance Score"
                                value={sourceContext.relevanceScore ? `${(sourceContext.relevanceScore * 100).toFixed(1)}%` : 'N/A'}
                                valueClass="text-green-400" />
                            <button className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 text-sm transition-colors">
                                <span className="material-symbols-outlined text-sm">download</span>
                                Download Original PDF
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-600 text-sm text-center px-8">
                        <div>
                            <span className="material-symbols-outlined text-4xl mb-2 block">find_in_page</span>
                            <p>Ask a question to see source context and citations here</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function MessageBubble({ message, onOpenViewer }) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-blue-600'
                }`}>
                <span className="text-white text-xs font-bold">{isUser ? 'ME' : 'Ai'}</span>
            </div>

            {/* Bubble */}
            <div className={`max-w-[70%] ${isUser
                    ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3'
                    : 'bg-surface-dark border border-gray-700 text-gray-200 rounded-2xl rounded-tl-none px-4 py-3'
                }`}>
                <div className="text-sm whitespace-pre-wrap" dangerouslySetInnerHTML={{
                    __html: formatMessage(message.content)
                }} />

                {/* Citations */}
                {message.citations?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-600">
                        <p className="text-xs text-gray-500 mb-1">Sources:</p>
                        {message.citations.map((c, i) => (
                            <span key={i} className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 cursor-pointer mr-2">
                                <span className="material-symbols-outlined text-xs">description</span>
                                {c.filename}{c.page_number ? `, Page ${c.page_number}` : ''}
                            </span>
                        ))}
                    </div>
                )}

                {/* Action buttons */}
                {message.citations?.length > 0 && (
                    <div className="flex gap-2 mt-2">
                        <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-700/50 hover:bg-gray-700 text-xs text-gray-300 transition-colors">
                            <span className="material-symbols-outlined text-xs">article</span>
                            View Full Report
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

function MetaRow({ label, value, valueClass = 'text-gray-300' }) {
    return (
        <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">{label}</span>
            <span className={`text-sm font-medium ${valueClass}`}>{value}</span>
        </div>
    );
}

function formatMessage(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-400 underline">$1</a>')
        .replace(/^- /gm, '• ')
        .replace(/\n/g, '<br/>');
}
