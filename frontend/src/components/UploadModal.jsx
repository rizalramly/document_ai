import { useState, useRef, useEffect } from 'react';
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocuments } from '../api';

export default function UploadModal({ onClose, onComplete }) {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState(null);

    const onDrop = useCallback((accepted) => {
        setFiles((prev) => [...prev, ...accepted.filter((f) => f.name.endsWith('.pdf'))]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: true,
    });

    const handleUpload = async () => {
        if (files.length === 0) return;
        setUploading(true);
        setProgress(0);
        try {
            const res = await uploadDocuments(files, (e) => {
                setProgress(Math.round((e.loaded * 100) / e.total));
            });
            setResult(res.data);
        } catch (err) {
            setResult({ error: err.response?.data?.detail || err.message });
        }
        setUploading(false);
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-surface-dark border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl">
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-blue-400">upload_file</span>
                        Upload PDF Documents
                    </h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="p-6">
                    {!result ? (
                        <>
                            {/* Drop zone */}
                            <div {...getRootProps()}
                                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'
                                    }`}>
                                <input {...getInputProps()} />
                                <span className="material-symbols-outlined text-4xl text-gray-500 mb-2 block">cloud_upload</span>
                                <p className="text-gray-400">Drag & drop PDF files here, or click to browse</p>
                                <p className="text-xs text-gray-600 mt-1">Supports: PDF documents, P&IDs, technical drawings</p>
                            </div>

                            {/* File list */}
                            {files.length > 0 && (
                                <div className="mt-4 space-y-2 max-h-40 overflow-y-auto">
                                    {files.map((f, i) => (
                                        <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2 text-sm">
                                            <span className="text-gray-300 truncate">{f.name}</span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-gray-500">{(f.size / 1024 / 1024).toFixed(1)} MB</span>
                                                <button onClick={() => setFiles(files.filter((_, j) => j !== i))}
                                                    className="text-gray-500 hover:text-red-400">
                                                    <span className="material-symbols-outlined text-sm">close</span>
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Progress */}
                            {uploading && (
                                <div className="mt-4">
                                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-500 transition-all rounded-full" style={{ width: `${progress}%` }} />
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1 text-center">{progress}% uploaded</p>
                                </div>
                            )}

                            <button onClick={handleUpload} disabled={files.length === 0 || uploading}
                                className="mt-4 w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                {uploading ? 'Uploading & Processing...' : `Upload ${files.length} file(s)`}
                            </button>
                        </>
                    ) : (
                        <div>
                            {result.error ? (
                                <div className="text-red-400 text-center py-4">
                                    <span className="material-symbols-outlined text-4xl mb-2 block">error</span>
                                    <p>{result.error}</p>
                                </div>
                            ) : (
                                <div className="text-center py-4">
                                    <span className="material-symbols-outlined text-4xl text-green-400 mb-2 block">check_circle</span>
                                    <p className="text-green-400 font-medium">Upload Complete</p>
                                    <p className="text-sm text-gray-400 mt-2">
                                        {result.total_uploaded} uploaded, {result.duplicates_skipped} duplicates skipped
                                    </p>
                                    <div className="mt-4 space-y-1 max-h-40 overflow-y-auto text-left">
                                        {result.results?.map((r, i) => (
                                            <div key={i} className={`text-xs px-3 py-1.5 rounded ${r.status === 'ready' ? 'bg-green-900/30 text-green-300' :
                                                    r.status === 'skipped' ? 'bg-yellow-900/30 text-yellow-300' :
                                                        'bg-red-900/30 text-red-300'
                                                }`}>
                                                {r.filename}: {r.message}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            <button onClick={onComplete}
                                className="mt-4 w-full py-3 rounded-lg bg-gray-700 hover:bg-gray-600 text-white font-medium transition-colors">
                                Done
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
