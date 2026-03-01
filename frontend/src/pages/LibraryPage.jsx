import { useState, useEffect, useCallback } from 'react';
import { getStats, getDocuments, uploadDocuments, refreshDB, removeDuplicates, deleteAll } from '../api';
import UploadModal from '../components/UploadModal';

export default function LibraryPage({ onOpenViewer }) {
    const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0, clusters: [], stations: [], units: [], doc_types: [] });
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filters, setFilters] = useState({ station: '', unit: '', doc_type: '' });
    const [showUpload, setShowUpload] = useState(false);
    const [actionLoading, setActionLoading] = useState('');
    const [activeCluster, setActiveCluster] = useState('');

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [statsRes, docsRes] = await Promise.all([
                getStats(),
                getDocuments({ search, ...filters, cluster: activeCluster, page: 1, page_size: 20 }),
            ]);
            setStats(statsRes.data);
            setDocuments(docsRes.data.documents);
        } catch (err) {
            console.error('Failed to fetch data:', err);
        }
        setLoading(false);
    }, [search, filters, activeCluster]);

    useEffect(() => { fetchData(); }, [fetchData]);

    const handleAction = async (action, label) => {
        if (action === deleteAll && !window.confirm('Are you sure you want to delete ALL documents? This cannot be undone.')) return;
        setActionLoading(label);
        try {
            const res = await action();
            alert(`${label}: ${res.data.message}`);
            fetchData();
        } catch (err) {
            alert(`${label} failed: ${err.response?.data?.detail || err.message}`);
        }
        setActionLoading('');
    };

    return (
        <div className="h-full overflow-y-auto px-6 pt-24 pb-3">
            {/* Header Row */}
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                        <span className="material-symbols-outlined text-xl text-white">description</span>
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">DOCS.ai</h1>
                        <p className="text-gray-400 text-xs">Browse and search through Engineering documents/drawing/P&IDs</p>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                    <ActionBtn icon="refresh" label="Refresh DB" color="bg-green-600 hover:bg-green-700"
                        loading={actionLoading === 'Refresh DB'}
                        onClick={() => handleAction(refreshDB, 'Refresh DB')} />
                    <ActionBtn icon="content_copy" label="Remove Duplicates" color="bg-orange-600 hover:bg-orange-700"
                        loading={actionLoading === 'Remove Duplicates'}
                        onClick={() => handleAction(removeDuplicates, 'Remove Duplicates')} />
                    <ActionBtn icon="delete_forever" label="Delete All" color="bg-red-600 hover:bg-red-700"
                        loading={actionLoading === 'Delete All'}
                        onClick={() => handleAction(deleteAll, 'Delete All')} />
                    <ActionBtn icon="upload_file" label="Upload PDF(s)" color="bg-blue-600 hover:bg-blue-700"
                        onClick={() => setShowUpload(true)} />
                </div>
            </div>

            {/* TED TNB GENCO Logo - top right in gap area */}
            <div className="absolute top-4 right-6">
                <img src="/images/ted-tnb-logo.png" alt="TED TNB GENCO" className="h-12 object-contain" />
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-gradient-to-r from-blue-600/80 to-blue-500/60 rounded-xl p-4 relative overflow-hidden">
                    <div className="relative z-10">
                        <p className="text-blue-100 text-xs font-medium">Total Documents</p>
                        <p className="text-3xl font-bold text-white mt-0.5">{stats.total_documents.toLocaleString()}</p>
                    </div>
                    <span className="material-symbols-outlined absolute right-3 top-3 text-5xl text-blue-400/30">description</span>
                </div>
                <div className="bg-gradient-to-r from-purple-600/80 to-purple-500/60 rounded-xl p-4 relative overflow-hidden">
                    <div className="relative z-10">
                        <p className="text-purple-100 text-xs font-medium">Total Chunks</p>
                        <p className="text-3xl font-bold text-white mt-0.5">{stats.total_chunks.toLocaleString()}</p>
                    </div>
                    <span className="material-symbols-outlined absolute right-3 top-3 text-5xl text-purple-400/30">data_array</span>
                </div>
            </div>

            {/* Intelligent Clusters */}
            <div className="mb-3">
                <h2 className="text-sm font-bold text-white mb-2">Intelligent Clusters</h2>
                <div className="flex flex-wrap gap-2">
                    {(stats.clusters.length > 0 ? stats.clusters : defaultClusters).map((c) => (
                        <button key={c.name}
                            onClick={() => setActiveCluster(activeCluster === c.name ? '' : c.name)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${activeCluster === c.name
                                ? 'bg-blue-500/20 border-blue-500 text-blue-300'
                                : 'bg-surface-dark border-gray-700 text-gray-300 hover:border-gray-500'
                                }`}>
                            <span className="material-symbols-outlined text-base" style={{ color: clusterColor(c.name) }}>folder</span>
                            {c.name}
                            <span className="text-xs bg-gray-800 px-2 py-0.5 rounded">{c.count}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Search */}
            <div className="relative mb-3">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-gray-500 text-lg">search</span>
                <input type="text" placeholder="Search Documents based on content"
                    value={search} onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-surface-dark border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors" />
            </div>

            {/* Filters */}
            <div className="bg-surface-dark border border-gray-700 rounded-lg p-3 mb-3">
                <div className="flex items-center gap-3 flex-wrap">
                    <span className="flex items-center gap-1 text-gray-400 text-xs">
                        <span className="material-symbols-outlined text-sm">filter_alt</span> Filters:
                    </span>
                    <FilterSelect label="All Stations" value={filters.station}
                        options={stats.stations} onChange={(v) => setFilters({ ...filters, station: v })} />
                    <FilterSelect label="All Units" value={filters.unit}
                        options={stats.units} onChange={(v) => setFilters({ ...filters, unit: v })} />
                </div>
                <div className="mt-2">
                    <FilterSelect label="All Event Types" value={filters.doc_type}
                        options={stats.doc_types} onChange={(v) => setFilters({ ...filters, doc_type: v })} full />
                </div>
            </div>

            {/* Document Tiles */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pb-6">
                {loading ? (
                    <>
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </>
                ) : documents.length > 0 ? (
                    documents.map((doc) => (
                        <DocumentTile key={doc.id} doc={doc} onOpenViewer={onOpenViewer} />
                    ))
                ) : (
                    <div className="col-span-2 text-center py-12 text-gray-500">
                        <span className="material-symbols-outlined text-6xl mb-4 block">folder_off</span>
                        <p className="text-lg">No documents found</p>
                        <p className="text-sm mt-1">Upload PDFs using the button above to get started</p>
                    </div>
                )}
            </div>

            {/* Upload Modal */}
            {showUpload && (
                <UploadModal onClose={() => setShowUpload(false)} onComplete={() => { setShowUpload(false); fetchData(); }} />
            )}
        </div>
    );
}

/* ── Sub-components ─────────────────────────────────────────── */

function ActionBtn({ icon, label, color, onClick, loading }) {
    return (
        <button onClick={onClick} disabled={loading}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-all ${color} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <span className="material-symbols-outlined text-base">{loading ? 'hourglass_empty' : icon}</span>
            {label}
        </button>
    );
}

function DocumentTile({ doc, onOpenViewer }) {
    const typeColors = {
        manual: 'bg-blue-900 text-blue-200', pid: 'bg-green-900 text-green-200',
        spec: 'bg-yellow-900 text-yellow-200', report: 'bg-red-900 text-red-200',
        drawing: 'bg-purple-900 text-purple-200', other: 'bg-gray-800 text-gray-300',
    };

    return (
        <div className="bg-surface-dark rounded-xl border border-gray-700 shadow-sm card-hover flex flex-col group cursor-pointer"
            onClick={() => onOpenViewer(doc)}>
            <div className="p-4 flex-1">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-white leading-snug group-hover:text-blue-400 transition-colors">
                        {doc.short_summary || doc.original_filename}
                    </h3>
                    <span className={`ml-2 inline-flex items-center px-2 py-1 rounded text-xs font-medium uppercase tracking-wide ${typeColors[doc.doc_type] || typeColors.other}`}>
                        {doc.doc_type || 'PDF'}
                    </span>
                </div>
                <div className="mb-2">
                    <div className="flex items-center text-xs text-yellow-500 mb-1 font-medium">
                        <span className="material-symbols-outlined text-sm mr-1">business</span>
                        {doc.project_name || 'Project name'}
                    </div>
                    <div className="text-xs text-gray-500 truncate font-mono">File: {doc.original_filename}</div>
                </div>
                <div className="flex flex-wrap gap-2 mb-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-yellow-900/30 text-yellow-300 border border-yellow-800">
                        {doc.doc_type ? doc.doc_type.charAt(0).toUpperCase() + doc.doc_type.slice(1) : 'Document Type'}
                    </span>
                    {doc.doc_date && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-300 border border-gray-700">
                            {new Date(doc.doc_date).toLocaleDateString()}
                        </span>
                    )}
                </div>
                <p className="text-sm text-gray-400 line-clamp-3">
                    {doc.purpose ? (
                        <>
                            <strong>Purpose:</strong> {doc.purpose}
                            {doc.tech_summary && <><br /><strong>Technical:</strong> {doc.tech_summary}</>}
                            {doc.location && <><br /><strong>Location:</strong> {doc.location}</>}
                        </>
                    ) : (
                        <>Summary of documents consist of<br />1. Document purpose<br />2. Important technical summary & 3. Project Location (if any)</>
                    )}
                </p>
            </div>
        </div>
    );
}

function FilterSelect({ label, value, options, onChange, full }) {
    return (
        <select value={value} onChange={(e) => onChange(e.target.value)}
            className={`bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500 ${full ? 'w-full' : ''}`}>
            <option value="">{label}</option>
            {(options || []).map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
    );
}

function SkeletonCard() {
    return (
        <div className="bg-surface-dark rounded-xl border border-gray-700 p-4">
            <div className="flex justify-between mb-4">
                <div className="h-5 w-48 skeleton rounded" />
                <div className="h-5 w-12 skeleton rounded" />
            </div>
            <div className="h-3 w-32 skeleton rounded mb-2" />
            <div className="h-3 w-full skeleton rounded mb-2" />
            <div className="flex gap-2 mb-4">
                <div className="h-5 w-20 skeleton rounded" />
                <div className="h-5 w-24 skeleton rounded" />
            </div>
            <div className="h-16 skeleton rounded" />
        </div>
    );
}

const defaultClusters = [
    { name: 'Boiler System', count: 42 },
    { name: 'Turbine Manuals', count: 18 },
    { name: 'Safety Incident Reports', count: 105 },
    { name: 'Environmental Specs', count: 50 },
];

function clusterColor(name) {
    const colors = { 'Boiler System': '#eab308', 'Turbine Manuals': '#3b82f6', 'Safety Incident Reports': '#ef4444', 'Environmental Specs': '#22c55e' };
    return colors[name] || '#6b7280';
}
