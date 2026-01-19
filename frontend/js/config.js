/**
 * PathPilot Configuration
 * API URL is determined based on the current environment
 */

// Determine API URL based on environment
const getApiBaseUrl = () => {
    const hostname = window.location.hostname;

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
    }

    // Production - use environment variable or construct from hostname
    // Railway backend URL pattern: https://pathpilot-backend-production.up.railway.app
    // Replace 'frontend' with 'backend' in the URL or use a fixed backend URL

    // Option 1: Use a fixed production backend URL (set this after deployment)
    const PRODUCTION_BACKEND_URL = window.PATHPILOT_API_URL || null;
    if (PRODUCTION_BACKEND_URL) {
        return PRODUCTION_BACKEND_URL;
    }

    // Option 2: Construct backend URL from frontend URL
    // If frontend is at pathpilot-frontend.up.railway.app
    // Backend would be at pathpilot-backend.up.railway.app
    const backendHost = hostname.replace('-frontend', '-backend').replace('frontend', 'backend');
    return `https://${backendHost}/api/v1`;
};

const API_BASE_URL = getApiBaseUrl();

console.log('PathPilot API URL:', API_BASE_URL);
