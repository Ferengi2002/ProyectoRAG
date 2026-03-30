document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatList = document.getElementById('chatList');
    
    // Auto-resize textarea
    questionInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        if (this.value.trim() !== '') {
            sendBtn.removeAttribute('disabled');
        } else {
            sendBtn.setAttribute('disabled', 'true');
        }
    });
    
    // Submit on Enter (sin Shift)
    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== '') {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });
    
    // Configurar el parseador de Markdown (usar DOMPurify si es producción)
    marked.setOptions({
        breaks: true,
        gfm: true,
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Disable input while processing
        questionInput.value = '';
        questionInput.style.height = 'auto';
        questionInput.setAttribute('disabled', 'true');
        sendBtn.setAttribute('disabled', 'true');
        
        // 1. Mostrar mensaje del usuario
        appendUserMessage(question);
        
        // 2. Mostrar indicador de carga del bot
        const loadingId = createTypingIndicator();
        
        try {
            // 3. Llamada Fetch al Backend FastAPI
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pregunta: question })
            });
            
            removeElement(loadingId);
            
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Error de red');
            }
            
            const data = await response.json();
            
            // 4. Mostrar la respuesta de la IA
            appendBotMessage(data.respuesta, data.fuentes);
            
        } catch (error) {
            console.error('Error al consultar RAG:', error);
            removeElement(loadingId);
            appendBotMessage(`Hubo un error procesando su solicitud: ${error.message}. Por favor, intente nuevamente.`);
        } finally {
            // Re-enable input
            questionInput.removeAttribute('disabled');
            questionInput.focus();
        }
    });
    
    // --- Helper Functions ---
    
    function appendUserMessage(text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper user';
        
        // Avatar del usuario
        const avatar = document.createElement('div');
        avatar.className = 'avatar user-avatar';
        avatar.textContent = 'U';
        
        // Contenido
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;
        
        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        chatList.appendChild(wrapper);
        scrollToBottom();
    }
    
    function appendBotMessage(markdownText, fuentesLista = []) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper bot';
        
        // Avatar del bot (Banco Pichincha)
        const avatar = document.createElement('div');
        avatar.className = 'avatar bot-avatar';
        avatar.textContent = 'BP';
        
        // Contenido
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Renderizar Markdown a HTML seguro
        content.innerHTML = marked.parse(markdownText);
        
        // Anexar Fuentes Citadas (Si existen)
        if (fuentesLista && fuentesLista.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            
            const sourcesTitle = document.createElement('div');
            sourcesTitle.className = 'sources-title';
            sourcesTitle.innerHTML = `<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg> Documentes Normativos Citados:`;
            
            sourcesDiv.appendChild(sourcesTitle);
            
            fuentesLista.forEach(fuente => {
                const span = document.createElement('span');
                span.className = 'source-item';
                span.textContent = fuente;
                sourcesDiv.appendChild(span);
            });
            
            content.appendChild(sourcesDiv);
        }
        
        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        chatList.appendChild(wrapper);
        scrollToBottom();
    }
    
    function createTypingIndicator() {
        const id = 'loading-' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper bot';
        wrapper.id = id;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar bot-avatar';
        avatar.textContent = 'BP';
        
        const content = document.createElement('div');
        content.className = 'message-content typing-indicator';
        
        // Tres puntos animados
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            content.appendChild(dot);
        }
        
        wrapper.appendChild(avatar);
        wrapper.appendChild(content);
        chatList.appendChild(wrapper);
        scrollToBottom();
        
        return id;
    }
    
    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
    
    function scrollToBottom() {
        chatList.scrollTop = chatList.scrollHeight;
    }
});
