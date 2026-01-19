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

    // Production backend URL
    return 'https://proud-exploration-production-2f38.up.railway.app/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

console.log('PathPilot API URL:', API_BASE_URL);
