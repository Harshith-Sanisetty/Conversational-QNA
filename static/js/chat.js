class ChatUI {
    constructor() {
        this.init();
        this.events();
        this.sid = null;
        this.uname = 'User';
        this.showAn = false;
    }

    init() {
        this.elWelcome = document.getElementById('welcome-screen');
        this.elChat = document.getElementById('chat-interface');
        this.elForm = document.getElementById('start-form');
        this.elUnameIn = document.getElementById('user-name');
        this.elMsgIn = document.getElementById('message-input');
        this.elSendBtn = document.getElementById('send-btn');
        this.elMessages = document.getElementById('chat-messages');
        this.elTyping = document.getElementById('typing-indicator');
        this.elUnameOut = document.getElementById('user-display');
        this.elSessInfo = document.getElementById('session-info');
        this.elAnPanel = document.getElementById('analysis-panel');
        this.elSummBtn = document.getElementById('summary-btn');
        this.elClearBtn = document.getElementById('clear-btn');
        this.elToggleAnBtn = document.getElementById('toggle-analysis');
    }

    events() {
        this.elForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.start();
        });

        this.elMsgIn.addEventListener('input', () => {
            this.elSendBtn.disabled = !this.elMsgIn.value.trim();
        });

        this.elMsgIn.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && this.elMsgIn.value.trim()) {
                e.preventDefault();
                this.send();
            }
        });

        this.elSendBtn.addEventListener('click', () => this.send());
        this.elSummBtn.addEventListener('click', () => this.cmd('/summary'));
        this.elClearBtn.addEventListener('click', () => this.clear());
        this.elToggleAnBtn.addEventListener('click', () => this.toggleAn());
    }

    async start() {
        const uname = this.elUnameIn.value.trim() || 'User';
        try {
            const resp = await fetch('/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ uname: uname })
            });
            const d = await resp.json();
            if (d.ok) {
                this.sid = d.sid;
                this.uname = uname;
                this.elWelcome.classList.add('hidden');
                this.elChat.classList.remove('hidden');
                this.elUnameOut.textContent = uname;
                this.elSessInfo.textContent = 'Active';
                this.addMsg(d.msg, 'bot');
                this.elMsgIn.focus();
                this.elAnPanel.classList.remove('hidden');
            } else {
                this.err('Start failed: ' + d.err);
            }
        } catch (e) {
            this.err('Error: ' + e.message);
        }
    }

    async send() {
        const msg = this.elMsgIn.value.trim();
        if (!msg) return;

        this.elMsgIn.value = '';
        this.elSendBtn.disabled = true;
        this.addMsg(msg, 'user');
        this.showTyping();

        try {
            const resp = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ msg: msg })
            });
            const d = await resp.json();
            this.hideTyping();
            if (d.ok) {
                this.addMsg(d.msg, 'bot', d.type);
                if (d.an) this.updateAn(d.an);
            } else {
                this.err('Error: ' + d.err);
            }
        } catch (e) {
            this.hideTyping();
            this.err('Network error: ' + e.message);
        }
        this.elMsgIn.focus();
    }

    async cmd(command) {
        this.elMsgIn.value = command;
        await this.send();
    }

    addMsg(txt, author, type = null) {
        const div = document.createElement('div');
        div.className = 'message';
        div.classList.add(author === 'user' ? 'user-message' : 'bot-message');

        if (author === 'bot' && type) {
            div.classList.add(`${type}-message`);
        }

        div.innerHTML = `${this.fmtMsg(txt)}<small class="timestamp">${this.getTime()}</small>`;
        this.elMessages.appendChild(div);
        this.scroll();
    }

    fmtMsg(txt) {
        return txt
            .replace(/\n/g, '<br>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>');
    }

    updateAn(an) {
        document.getElementById('topic-value').textContent = an.topic || '-';
        document.getElementById('sentiment-value').textContent = an.mood || '-';
        document.getElementById('keywords-value').textContent = an.kws?.join(', ') || '-';
        document.getElementById('context-score').textContent = an.score ? an.score.toFixed(2) : '-';
    }

    showTyping() {
        this.elTyping.classList.remove('hidden');
    }

    hideTyping() {
        this.elTyping.classList.add('hidden');
    }

    scroll() {
        this.elMessages.scrollTop = this.elMessages.scrollHeight;
    }

    getTime() {
        return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    err(msg) {
        this.addMsg(`❌ ${msg}`, 'bot');
    }

    toggleAn() {
        this.showAn = !this.showAn;
        const c = this.elAnPanel.querySelector('.analysis-content');
        if (this.showAn) {
            c.style.display = 'grid';
            this.elToggleAnBtn.textContent = 'Hide Analysis';
        } else {
            c.style.display = 'none';
            this.elToggleAnBtn.textContent = 'Show Analysis';
        }
    }

    async clear() {
        if (!confirm('Start a new session? This clears the current chat.')) return;
        try {
            const resp = await fetch('/clear', { method: 'POST' });
            const d = await resp.json();
            if (d.ok) {
                this.elMessages.innerHTML = '';
                this.sid = null;
                this.elChat.classList.add('hidden');
                this.elAnPanel.classList.add('hidden');
                this.elWelcome.classList.remove('hidden');
                this.elUnameIn.value = '';
            } else {
                this.err('Failed to clear session: ' + d.err);
            }
        } catch (e) {
            this.err('Error clearing session: ' + e.message);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => new ChatUI());

document.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON') {
        e.target.style.transform = 'scale(0.98)';
        setTimeout(() => { e.target.style.transform = ''; }, 100);
    }
});

document.addEventListener('input', (e) => {
    if (e.target.id === 'message-input') {
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 100)}px`;
    }
});