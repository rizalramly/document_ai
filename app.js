// ===== DOCS.ai Application Logic =====

document.addEventListener('DOMContentLoaded', () => {
    // --- Tab / Page Navigation ---
    const navLinks = document.querySelectorAll('[data-page]');
    const pageViews = document.querySelectorAll('.page-view');

    function switchPage(pageId) {
        // Hide all pages - remove active class AND set inline style
        pageViews.forEach(p => {
            p.classList.remove('active');
            p.style.display = 'none';
        });
        // Deactivate all nav links
        navLinks.forEach(l => {
            l.classList.remove('bg-blue-500/10', 'text-blue-400', 'border-blue-500/20', 'bg-primary/10', 'border', 'border-primary/20');
            l.classList.add('text-slate-400', 'hover:bg-slate-800/50');
        });
        // Show target page - add active class AND set inline style
        const target = document.getElementById(pageId);
        if (target) {
            target.classList.add('active');
            target.style.display = 'flex';
        }
        // Highlight active nav
        const activeLink = document.querySelector(`[data-page="${pageId}"]`);
        if (activeLink) {
            activeLink.classList.remove('text-slate-400', 'hover:bg-slate-800/50');
            activeLink.classList.add('bg-blue-500/10', 'text-blue-400', 'border', 'border-blue-500/20');
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchPage(link.dataset.page);
        });
    });

    // --- Sidebar Toggle ---
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar-collapsed');
        });
    }

    // --- Dark / Light Mode Toggle ---
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
        });
    }

    // --- Chatbot: Simulated Send ---
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send');
    const chatMessages = document.getElementById('chat-messages');

    function addChatMessage(text, isUser = true) {
        const wrapper = document.createElement('div');
        wrapper.className = isUser
            ? 'flex gap-4 max-w-3xl ml-auto flex-row-reverse fade-in'
            : 'flex gap-4 max-w-3xl fade-in';

        const avatar = document.createElement('div');
        if (isUser) {
            avatar.className = 'w-8 h-8 rounded-full bg-slate-600 flex-shrink-0 flex items-center justify-center text-slate-200 text-xs';
            avatar.textContent = 'ME';
        } else {
            avatar.className = 'w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white text-xs';
            avatar.textContent = 'AI';
        }

        const bubble = document.createElement('div');
        bubble.className = isUser
            ? 'bg-blue-500 text-white rounded-2xl rounded-tr-none p-4 shadow-sm text-sm leading-relaxed'
            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none p-4 shadow-sm text-sm leading-relaxed text-slate-700 dark:text-slate-200';

        const p = document.createElement('p');
        p.textContent = text;
        bubble.appendChild(p);

        const msgDiv = document.createElement('div');
        msgDiv.className = 'space-y-2';
        msgDiv.appendChild(bubble);

        wrapper.appendChild(avatar);
        wrapper.appendChild(msgDiv);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex gap-4 max-w-3xl fade-in';
        wrapper.id = 'typing-indicator';

        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex-shrink-0 flex items-center justify-center text-white text-xs">AI</div>
            <div class="space-y-2">
                <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm flex items-center gap-1">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>`;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const ind = document.getElementById('typing-indicator');
        if (ind) ind.remove();
    }

    if (chatSendBtn && chatInput) {
        const sendMessage = () => {
            const text = chatInput.value.trim();
            if (!text) return;
            addChatMessage(text, true);
            chatInput.value = '';
            showTypingIndicator();
            setTimeout(() => {
                removeTypingIndicator();
                addChatMessage("I'm currently in UI preview mode. RAG backend integration will be connected soon. Your query has been noted.", false);
            }, 1500);
        };
        chatSendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    }

    // --- Viewer: Simulated Chat Send ---
    const viewerChatInput = document.getElementById('viewer-chat-input');
    const viewerChatSend = document.getElementById('viewer-chat-send');
    const viewerChatMessages = document.getElementById('viewer-chat-messages');

    if (viewerChatSend && viewerChatInput && viewerChatMessages) {
        const sendViewerMsg = () => {
            const text = viewerChatInput.value.trim();
            if (!text) return;
            // User message
            const userMsg = document.createElement('div');
            userMsg.className = 'flex items-start space-x-3 flex-row-reverse space-x-reverse fade-in';
            userMsg.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gray-600 flex-shrink-0 flex items-center justify-center text-white text-xs">EU</div>
                <div class="flex flex-col space-y-1 max-w-[85%] items-end">
                    <div class="bg-blue-500/20 rounded-lg rounded-tr-none p-3 border border-blue-500/30 text-sm text-white shadow-sm"><p>${text}</p></div>
                    <span class="text-[10px] text-gray-500">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>`;
            viewerChatMessages.appendChild(userMsg);
            viewerChatInput.value = '';
            viewerChatMessages.scrollTop = viewerChatMessages.scrollHeight;

            // AI response
            setTimeout(() => {
                const aiMsg = document.createElement('div');
                aiMsg.className = 'flex items-start space-x-3 fade-in';
                aiMsg.innerHTML = `
                    <div class="w-8 h-8 rounded bg-blue-500 flex-shrink-0 flex items-center justify-center text-white"><span class="material-symbols-outlined text-sm">smart_toy</span></div>
                    <div class="flex flex-col space-y-1 max-w-[85%]">
                        <div class="bg-[#2a2d3d] rounded-lg rounded-tl-none p-3 border border-gray-700 text-sm text-gray-200 shadow-sm"><p>I'm in preview mode. Drawing analysis will be available once the RAG backend is connected.</p></div>
                        <span class="text-[10px] text-gray-500">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>`;
                viewerChatMessages.appendChild(aiMsg);
                viewerChatMessages.scrollTop = viewerChatMessages.scrollHeight;
            }, 1200);
        };
        viewerChatSend.addEventListener('click', sendViewerMsg);
        viewerChatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendViewerMsg(); }
        });
    }

    // --- Viewer Toolbar ---
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // --- Zoom Slider Display ---
    const zoomSlider = document.getElementById('zoom-slider');
    const zoomValue = document.getElementById('zoom-value');
    if (zoomSlider && zoomValue) {
        zoomSlider.addEventListener('input', () => {
            zoomValue.textContent = zoomSlider.value + '%';
        });
    }

    // --- Search bar interaction ---
    const searchInput = document.getElementById('doc-search');
    if (searchInput) {
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.classList.add('ring-2', 'ring-blue-500');
        });
        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.classList.remove('ring-2', 'ring-blue-500');
        });
    }

    // Default page
    switchPage('page-library');
});
