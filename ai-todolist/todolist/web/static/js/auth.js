// 认证相关功能
document.addEventListener('DOMContentLoaded', () => {
    // 检查用户是否已登录
    function checkAuth() {
        // 如果没有token，重定向到登录页面
        if (!API.token && !window.location.href.includes('login.html') && !window.location.href.includes('register.html') && !window.location.href.includes('index.html')) {
            window.location.href = 'login.html';
            return false;
        }
        
        // 如果有token，但在登录/注册页面，重定向到仪表盘
        if (API.token && (window.location.href.includes('login.html') || window.location.href.includes('register.html'))) {
            window.location.href = 'dashboard.html';
            return true;
        }
        
        return true;
    }
    
    // 初始检查认证状态
    checkAuth();
    
    // 登录表单处理
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const errorElement = document.getElementById('login-error');
            errorElement.style.display = 'none';
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await API.auth.login({ username, password });
                
                // 保存token
                API.setToken(response.token);
                
                // 重定向到仪表盘
                window.location.href = 'dashboard.html';
            } catch (error) {
                errorElement.textContent = error.message || '登录失败，请检查用户名和密码';
                errorElement.style.display = 'block';
            }
        });
    }
    
    // 注册表单处理
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const errorElement = document.getElementById('register-error');
            errorElement.style.display = 'none';
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const passwordConfirm = document.getElementById('password_confirm').value;
            
            // 验证密码
            if (password !== passwordConfirm) {
                errorElement.textContent = '两次输入的密码不一致';
                errorElement.style.display = 'block';
                return;
            }
            
            if (password.length < 8) {
                errorElement.textContent = '密码长度不能少于8个字符';
                errorElement.style.display = 'block';
                return;
            }
            
            try {
                const response = await API.auth.register({ username, email, password });
                
                // 保存token
                API.setToken(response.token);
                
                // 重定向到仪表盘
                window.location.href = 'dashboard.html';
            } catch (error) {
                errorElement.textContent = error.message || '注册失败，请稍后再试';
                errorElement.style.display = 'block';
            }
        });
    }
    
    // 登出按钮处理
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // 清除token
            API.setToken(null);
            
            // 重定向到登录页
            window.location.href = 'login.html';
        });
    }
    
    // 加载用户信息
    const usernameElement = document.getElementById('username');
    if (usernameElement && API.token) {
        API.auth.getCurrentUser()
            .then(user => {
                usernameElement.textContent = user.username;
            })
            .catch(error => {
                console.error('获取用户信息失败:', error);
                // 如果获取用户信息失败，可能是token无效，清除token并重定向
                if (error.message === '无效或过期的令牌') {
                    API.setToken(null);
                    window.location.href = 'login.html';
                }
            });
    }
});