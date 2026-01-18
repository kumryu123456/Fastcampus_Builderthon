/**
 * Toast Notification System - PathPilot
 * Provides user-friendly notifications instead of alert()
 */

class Toast {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if not exists
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
            `;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const colors = {
            success: { bg: '#10b981', border: '#059669' },
            error: { bg: '#ef4444', border: '#dc2626' },
            warning: { bg: '#f59e0b', border: '#d97706' },
            info: { bg: '#6366f1', border: '#4f46e5' }
        };

        const color = colors[type] || colors.info;

        toast.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 20px;
            background: white;
            border-left: 4px solid ${color.bg};
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        `;

        toast.innerHTML = `
            <span style="
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: ${color.bg};
                color: white;
                border-radius: 50%;
                font-size: 14px;
                font-weight: bold;
            ">${icons[type]}</span>
            <span style="flex: 1; color: #1a1a2e; font-size: 14px; line-height: 1.4;">${message}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                font-size: 18px;
                padding: 0;
                line-height: 1;
            ">×</button>
        `;

        this.container.appendChild(toast);

        // Add animation styles if not exists
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Global toast instance
const toast = new Toast();

// Korean error messages
const ErrorMessages = {
    NETWORK_ERROR: '네트워크 연결을 확인해주세요.',
    SERVER_ERROR: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
    VALIDATION_ERROR: '입력 정보를 확인해주세요.',
    NOT_FOUND: '요청한 데이터를 찾을 수 없습니다.',
    GENERATION_FAILED: '생성에 실패했습니다. 다시 시도해주세요.',
    UPLOAD_FAILED: '파일 업로드에 실패했습니다.',
    FILE_TOO_LARGE: '파일 크기가 너무 큽니다. (최대 5MB)',
    INVALID_FILE_TYPE: '지원하지 않는 파일 형식입니다. (PDF, DOCX만 가능)',
    SESSION_EXPIRED: '세션이 만료되었습니다. 페이지를 새로고침 해주세요.',
};

// Helper function to handle API errors
function handleApiError(error, fallbackMessage = '오류가 발생했습니다.') {
    console.error('API Error:', error);

    if (error.message.includes('fetch')) {
        toast.error(ErrorMessages.NETWORK_ERROR);
    } else if (error.message.includes('500')) {
        toast.error(ErrorMessages.SERVER_ERROR);
    } else if (error.message.includes('404')) {
        toast.error(ErrorMessages.NOT_FOUND);
    } else if (error.message) {
        toast.error(error.message);
    } else {
        toast.error(fallbackMessage);
    }
}
