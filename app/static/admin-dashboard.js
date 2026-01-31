/**
 * Admin Dashboard JavaScript
 * Handles data fetching, animated counters, and UI updates
 */

// API endpoint
const API_BASE = '/api/v1/admin/stats';

// Animated counter function
function animateValue(element, start, end, duration = 2000) {
    if (start === end) {
        element.textContent = formatNumber(end);
        return;
    }
    
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = formatNumber(current);
    }, stepTime);
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Load dashboard statistics
async function loadStats() {
    const loadingEl = document.getElementById('loading');
    const contentEl = document.getElementById('dashboardContent');
    
    try {
        // Show loading
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        
        // Fetch data with credentials
        const response = await fetch(API_BASE, {
            method: 'GET',
            credentials: 'include', // Include cookies for authentication
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                // Not authenticated, redirect to login
                window.location.href = '/admin/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Dashboard stats loaded:', data);
        
        // Hide loading, show content
        loadingEl.style.display = 'none';
        contentEl.style.display = 'block';
        
        // Update all stats with animations
        updateStats(data);
        
    } catch (error) {
        console.error('Error loading stats:', error);
        loadingEl.innerHTML = `
            <div style="color: #DC2626;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px;"></i>
                <p>Error loading statistics</p>
                <p style="font-size: 14px; margin-top: 8px;">${error.message}</p>
                <button onclick="loadStats()" style="margin-top: 16px; padding: 10px 20px; background: #5B87F5; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Update all statistics
function updateStats(data) {
    // Main stats cards
    animateStatValue('.card-users .stat-value', data.users.total);
    animateStatValue('.card-active-users .stat-value', data.users.active);
    animateStatValue('.card-dealers .stat-value', data.users.dealers);
    animateStatValue('.card-ads .stat-value', data.ads.total);
    animateStatValue('.card-active-ads .stat-value', data.ads.active);
    animateStatValue('.card-pending .stat-value', data.ads.pending);
    animateStatValue('.card-messages .stat-value', data.chat.messages || 0);
    animateStatValue('.card-reports .stat-value', data.moderation.total_reports);
    
    // Secondary stats
    document.getElementById('newUsersWeek').textContent = formatNumber(data.users.new_week);
    document.getElementById('newAdsWeek').textContent = formatNumber(data.ads.new_week);
    document.getElementById('totalDialogs').textContent = formatNumber(data.chat.dialogs);
    document.getElementById('pendingReports').textContent = formatNumber(data.moderation.pending_reports);
    
    // Recent activity
    animateStatValue('#recentUsers', data.recent_activity.users_24h);
    animateStatValue('#recentAds', data.recent_activity.ads_24h);
    animateStatValue('#recentMessages', data.recent_activity.messages_24h);
    
    // Ad status breakdown
    animateStatValue('#statusActive', data.ads.by_status.active || 0);
    animateStatValue('#statusPending', data.ads.by_status.pending || 0);
    animateStatValue('#statusDraft', data.ads.by_status.draft || 0);
    animateStatValue('#statusRejected', data.ads.by_status.rejected || 0);
    
    // User role breakdown
    animateStatValue('#roleUser', data.users.by_role.user || 0);
    animateStatValue('#roleDealer', data.users.by_role.dealer || 0);
    animateStatValue('#roleModerator', data.users.by_role.moderator || 0);
    animateStatValue('#roleAdmin', data.users.by_role.admin || 0);
    
    // Interactions
    animateStatValue('#totalFavorites', data.interactions.favorites);
    animateStatValue('#totalComparisons', data.interactions.comparisons);
    animateStatValue('#totalViews', data.interactions.views);
}

// Animate stat value
function animateStatValue(selector, targetValue) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
    const target = parseInt(targetValue) || 0;
    
    animateValue(element, currentValue, target, 1500);
}

// Auto-refresh every 5 minutes
let refreshInterval;

function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadStats();
    }, 5 * 60 * 1000); // 5 minutes
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    startAutoRefresh();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});

