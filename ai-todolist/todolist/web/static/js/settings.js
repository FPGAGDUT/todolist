/**
 * AI TodoList 用户设置脚本
 * 负责处理用户设置和偏好管理
 */

document.addEventListener('DOMContentLoaded', function() {
    // 绑定设置按钮事件
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettings);
    }
    
    // 绑定关闭按钮
    const closeSettingsBtn = document.getElementById('settings-modal-close');
    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', closeSettings);
    }
    
    // 绑定取消按钮
    const cancelBtn = document.getElementById('settings-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeSettings);
    }
    
    // 绑定保存按钮
    const saveBtn = document.getElementById('settings-save');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveSettings);
    }
    
    // 绑定标签页切换
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有活动标签
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // 隐藏所有内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            // 激活当前标签
            this.classList.add('active');
            const tabId = this.dataset.tab;
            document.getElementById(`${tabId}-tab`).style.display = 'block';
        });
    });
    
    // 绑定密码更改按钮
    const changePasswordBtn = document.getElementById('change-password-btn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', changePassword);
    }
    
    // 绑定同步按钮
    const syncNowBtn = document.getElementById('sync-now-btn');
    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', syncData);
    }
    
    // 绑定导出按钮
    const exportDataBtn = document.getElementById('export-data-btn');
    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', exportData);
    }
    
    // 应用已保存的设置
    applyUserSettings();
});

/**
 * 打开设置模态框
 */
function openSettings() {
    document.getElementById('settings-modal').style.display = 'flex';
    
    // 加载用户当前设置
    loadUserSettings();
}

/**
 * 关闭设置模态框
 */
function closeSettings() {
    document.getElementById('settings-modal').style.display = 'none';
    
    // 重置表单状态
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
}

/**
 * 加载用户设置到表单
 */
function loadUserSettings() {
    // 尝试从本地存储加载设置
    const settings = getUserSettings();
    
    // 设置主题选择器
    if (settings.theme) {
        document.getElementById('theme-select').value = settings.theme;
    }
    
    // 设置语言选择器
    if (settings.language) {
        document.getElementById('language-select').value = settings.language;
    }
    
    // 设置自动同步开关
    if (settings.hasOwnProperty('autoSync')) {
        document.getElementById('auto-sync').checked = settings.autoSync;
    }
}

/**
 * 保存设置
 */
function saveSettings() {
    // 收集设置数据
    const settings = {
        theme: document.getElementById('theme-select').value,
        language: document.getElementById('language-select').value,
        autoSync: document.getElementById('auto-sync').checked
    };
    
    // 保存到服务器
    API.user.updateSettings(settings)
        .then(response => {
            console.log('设置已保存到服务器', response);
            
            // 同时保存到本地存储
            localStorage.setItem('user_settings', JSON.stringify(settings));
            
            // 应用设置
            applyUserSettings();
            
            // 关闭模态框
            closeSettings();
            
            // 显示成功消息
            showNotification('设置已保存', 'success');
        })
        .catch(error => {
            console.error('保存设置失败:', error);
            
            // 尝试保存到本地
            localStorage.setItem('user_settings', JSON.stringify(settings));
            
            // 应用设置
            applyUserSettings();
            
            // 关闭模态框
            closeSettings();
            
            // 显示警告消息
            showNotification('无法保存到服务器，已保存到本地', 'warning');
        });
}

/**
 * 应用用户设置到界面
 */
function applyUserSettings() {
    const settings = getUserSettings();
    
    // 应用主题
    if (settings.theme) {
        if (settings.theme === 'system') {
            // 检测系统主题
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', settings.theme);
        }
    }
    
    // 可以添加更多设置应用逻辑
}

/**
 * 从存储中获取用户设置
 */
function getUserSettings() {
    // 尝试从本地存储获取
    const storedSettings = localStorage.getItem('user_settings');
    
    // 默认设置
    const defaultSettings = {
        theme: 'light',
        language: 'zh-CN',
        autoSync: true
    };
    
    // 合并已存储设置和默认设置
    return storedSettings ? {...defaultSettings, ...JSON.parse(storedSettings)} : defaultSettings;
}

/**
 * 更改密码
 */
function changePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // 基本验证
    if (!currentPassword) {
        showNotification('请输入当前密码', 'error');
        return;
    }
    
    if (!newPassword) {
        showNotification('请输入新密码', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showNotification('两次输入的新密码不一致', 'error');
        return;
    }
    
    if (newPassword.length < 8) {
        showNotification('新密码长度应至少为8个字符', 'error');
        return;
    }
    
    // 发送请求
    API.user.changePassword(currentPassword, newPassword)
        .then(response => {
            // 清空表单
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-password').value = '';
            
            // 显示成功消息
            showNotification('密码已更新', 'success');
        })
        .catch(error => {
            console.error('更改密码失败:', error);
            
            // 显示错误消息
            if (error.message) {
                showNotification(error.message, 'error');
            } else {
                showNotification('更改密码失败，请重试', 'error');
            }
        });
}

/**
 * 同步数据
 */
function syncData() {
    // 显示同步中状态
    const syncBtn = document.getElementById('sync-now-btn');
    const originalText = syncBtn.textContent;
    syncBtn.innerHTML = '<i class="bi bi-arrow-repeat spinning"></i> 同步中...';
    syncBtn.disabled = true;
    
    // 模拟同步操作
    setTimeout(() => {
        // 更新同步时间
        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');
        document.getElementById('last-sync-time').textContent = timeString;
        document.getElementById('last-sync').textContent = `上次同步: ${timeString}`;
        
        // 恢复按钮状态
        syncBtn.innerHTML = originalText;
        syncBtn.disabled = false;
        
        // 显示成功消息
        showNotification('数据同步成功', 'success');
        
        // 重新加载任务数据
        if (typeof loadTaskData === 'function') {
            loadTaskData();
        }
    }, 1500);
}

/**
 * 导出数据
 */
function exportData() {
    // 创建导出数据
    const exportData = {
        tasks: window.allTasks || [],
        settings: getUserSettings(),
        exportDate: new Date().toISOString()
    };
    
    // 创建下载链接
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileName = `todolist_export_${new Date().toISOString().substring(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileName);
    linkElement.style.display = 'none';
    
    document.body.appendChild(linkElement);
    linkElement.click();
    document.body.removeChild(linkElement);
    
    // 显示成功消息
    showNotification('数据导出成功', 'success');
}

/**
 * 显示通知消息
 * 此函数可能与dashboard.js中的重复，但为了模块独立性保留
 */
function showNotification(message, type = 'info') {
    // 如果dashboard.js已加载且定义了showNotification函数，则使用它
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
        return;
    }
    
    // 否则使用自己的实现
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    let iconClass = 'bi-info-circle';
    if (type === 'success') iconClass = 'bi-check-circle';
    if (type === 'error') iconClass = 'bi-exclamation-circle';
    if (type === 'warning') iconClass = 'bi-exclamation-triangle';
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="bi ${iconClass}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close"><i class="bi bi-x"></i></button>
    `;
    
    document.body.appendChild(notification);
    
    // 绑定关闭按钮
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.remove();
    });
    
    // 自动关闭
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}