// API服务封装
const API = {
    baseUrl: 'http://127.0.0.1:8083/v1',
    token: null,
    
    // 初始化API - 从localStorage获取token
    init() {
        this.token = localStorage.getItem('auth_token');
    },
    
    // 设置token
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    },
    
    // 获取API请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    },
    
    // API请求方法
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders()
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.error || '请求失败');
            }
            
            return responseData;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    },
    
    // 认证相关API
    auth: {
        // 用户注册
        register(userData) {
            return API.request('/auth/register', 'POST', userData);
        },
        
        // 用户登录
        login(credentials) {
            return API.request('/auth/login', 'POST', credentials);
        },
        
        // 获取当前用户信息
        getCurrentUser() {
            return API.request('/users/me');
        },
        
        // 更新用户设置
        updateSettings(settings) {
            return API.request('/users/me/settings', 'PUT', settings);
        }
    },
    
    // 任务相关API
    tasks: {
        // 获取所有任务
        getAll(filters = {}) {
            let queryParams = '';
            if (Object.keys(filters).length > 0) {
                queryParams = '?' + new URLSearchParams(filters).toString();
            }
            return API.request(`/tasks${queryParams}`);
        },
        
        // 创建任务
        create(taskData) {
            return API.request('/tasks', 'POST', taskData);
        },
        
        // 更新任务
        update(taskId, taskData) {
            return API.request(`/tasks/${taskId}`, 'PUT', taskData);
        },
        
        // 删除任务
        delete(taskId) {
            return API.request(`/tasks/${taskId}`, 'DELETE');
        },
        
        // 批量操作
        batch(operations) {
            return API.request('/tasks/batch', 'POST', { operations });
        }
    }
};

// 页面加载时初始化API
document.addEventListener('DOMContentLoaded', () => {
    API.init();
});