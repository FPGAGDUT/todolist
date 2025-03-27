// 任务管理功能
document.addEventListener('DOMContentLoaded', () => {
    const taskList = document.getElementById('task-list');
    const taskForm = document.getElementById('task-form');
    const taskInput = document.getElementById('task-input');
    const currentViewTitle = document.getElementById('current-view-title');
    
    // 任务视图状态
    const state = {
        tasks: [],
        currentFilter: null,
        currentCategory: null,
        sortBy: 'date-asc',
        viewMode: 'list'
    };
    
    // 初始化任务列表
    function initTasks() {
        if (!taskList) return;
        
        // 显示加载指示器
        taskList.innerHTML = `
            <div class="loading-indicator">
                <div class="spinner"></div>
                <p>加载任务中...</p>
            </div>
        `;
        
        // 加载任务
        loadTasks();
        
        // 设置事件监听器
        setupEventListeners();
    }
    
    // 加载任务列表
    async function loadTasks() {
        try {
            // 构建过滤器
            const filters = {};
            
            if (state.currentCategory) {
                filters.category = state.currentCategory;
            }
            
            if (state.currentFilter === 'today') {
                const today = new Date().toISOString().split('T')[0];
                filters.due_date = today;
            } else if (state.currentFilter === 'upcoming') {
                // 服务器端需要支持upcoming过滤
                filters.upcoming = 'true';
            } else if (state.currentFilter === 'completed') {
                filters.completed = 'true';
            } else if (state.currentFilter === 'incomplete') {
                filters.completed = 'false';
            }
            
            // 获取任务
            const response = await API.tasks.getAll(filters);
            state.tasks = response.tasks;
            
            // 排序任务
            sortTasks();
            
            // 渲染任务
            renderTasks();
        } catch (error) {
            console.error('加载任务失败:', error);
            taskList.innerHTML = `
                <div class="error-message">
                    <p>加载任务失败: ${error.message}</p>
                    <button id="retry-load" class="btn btn-primary">重试</button>
                </div>
            `;
            
            // 添加重试按钮监听器
            document.getElementById('retry-load')?.addEventListener('click', loadTasks);
        }
    }
    
    // 排序任务
    function sortTasks() {
        switch (state.sortBy) {
            case 'date-asc':
                state.tasks.sort((a, b) => {
                    if (!a.due_date) return 1;
                    if (!b.due_date) return -1;
                    return new Date(a.due_date) - new Date(b.due_date);
                });
                break;
            case 'date-desc':
                state.tasks.sort((a, b) => {
                    if (!a.due_date) return 1;
                    if (!b.due_date) return -1;
                    return new Date(b.due_date) - new Date(a.due_date);
                });
                break;
            case 'priority':
                const priorityOrder = { '高': 0, '中': 1, '正常': 2, '低': 3 };
                state.tasks.sort((a, b) => {
                    return (priorityOrder[a.priority] || 999) - (priorityOrder[b.priority] || 999);
                });
                break;
            case 'category':
                state.tasks.sort((a, b) => a.category.localeCompare(b.category));
                break;
        }
    }
    
    // 渲染任务列表
    function renderTasks() {
        if (!taskList) return;
        
        if (state.tasks.length === 0) {
            taskList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-check2-all"></i>
                    <p>暂无任务</p>
                    <p class="hint">添加新任务开始使用吧！</p>
                </div>
            `;
            return;
        }
        
        // 根据视图模式渲染
        if (state.viewMode === 'list') {
            renderListView();
        } else {
            renderBoardView();
        }
    }
    
    // 列表视图渲染
    function renderListView() {
        let html = '';
        
        state.tasks.forEach(task => {
            const dueDate = task.due_date ? formatDate(task.due_date) : '';
            const dueTime = task.due_time || '';
            const priorityClass = getPriorityClass(task.priority);
            
            html += `
                <div class="task-item ${task.completed ? 'completed' : ''}" data-id="${task.id}">
                    <div class="task-checkbox">
                        <input type="checkbox" id="task-${task.id}" ${task.completed ? 'checked' : ''}>
                        <label for="task-${task.id}"></label>
                    </div>
                    <div class="task-content">
                        <div class="task-text">${task.text}</div>
                        <div class="task-meta">
                            <span class="task-category">${task.category}</span>
                            ${dueDate ? `<span class="task-due-date"><i class="bi bi-calendar"></i> ${dueDate}</span>` : ''}
                            ${dueTime ? `<span class="task-due-time"><i class="bi bi-clock"></i> ${dueTime}</span>` : ''}
                            <span class="task-priority ${priorityClass}">${task.priority}</span>
                        </div>
                    </div>
                    <div class="task-actions">
                        <button class="btn-icon task-edit" title="编辑"><i class="bi bi-pencil"></i></button>
                        <button class="btn-icon task-delete" title="删除"><i class="bi bi-trash"></i></button>
                    </div>
                </div>
            `;
        });
        
        taskList.innerHTML = html;
        
        // 添加任务项事件监听器
        addTaskItemListeners();
    }
    
    // 看板视图渲染
    function renderBoardView() {
        // 按类别分组
        const categories = {};
        state.tasks.forEach(task => {
            if (!categories[task.category]) {
                categories[task.category] = [];
            }
            categories[task.category].push(task);
        });
        
        let html = '<div class="task-board">';
        
        // 渲染每个类别列
        for (const category in categories) {
            html += `
                <div class="board-column" data-category="${category}">
                    <div class="column-header">
                        <h3>${category}</h3>
                        <span class="task-count">${categories[category].length}</span>
                    </div>
                    <div class="column-content">
            `;
            
            // 渲染该类别的任务
            categories[category].forEach(task => {
                const dueDate = task.due_date ? formatDate(task.due_date) : '';
                const priorityClass = getPriorityClass(task.priority);
                
                html += `
                    <div class="board-task ${task.completed ? 'completed' : ''}" data-id="${task.id}">
                        <div class="board-task-header">
                            <input type="checkbox" id="btask-${task.id}" ${task.completed ? 'checked' : ''}>
                            <label for="btask-${task.id}"></label>
                            <div class="task-actions">
                                <button class="btn-icon task-edit" title="编辑"><i class="bi bi-pencil"></i></button>
                                <button class="btn-icon task-delete" title="删除"><i class="bi bi-trash"></i></button>
                            </div>
                        </div>
                        <div class="board-task-content">
                            <p>${task.text}</p>
                        </div>
                        <div class="board-task-footer">
                            ${dueDate ? `<span class="task-due-date"><i class="bi bi-calendar"></i> ${dueDate}</span>` : ''}
                            <span class="task-priority ${priorityClass}">${task.priority}</span>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        taskList.innerHTML = html;
        
        // 添加任务项事件监听器
        addTaskItemListeners();
    }
    
    // 添加任务项事件监听器
    function addTaskItemListeners() {
        // 复选框状态变更
        document.querySelectorAll('.task-checkbox input, .board-task-header input').forEach(checkbox => {
            checkbox.addEventListener('change', async (e) => {
                const taskElement = e.target.closest('.task-item, .board-task');
                const taskId = taskElement.dataset.id;
                const completed = e.target.checked;
                
                try {
                    await API.tasks.update(taskId, { completed });
                    taskElement.classList.toggle('completed', completed);
                } catch (error) {
                    console.error('更新任务状态失败:', error);
                    e.target.checked = !completed; // 恢复复选框状态
                    showNotification('更新任务状态失败', 'error');
                }
            });
        });
        
        // 编辑按钮
        document.querySelectorAll('.task-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskElement = e.target.closest('.task-item, .board-task');
                const taskId = taskElement.dataset.id;
                const task = state.tasks.find(t => t.id === taskId);
                
                if (task) {
                    showEditTaskModal(task);
                }
            });
        });
        
        // 删除按钮
        document.querySelectorAll('.task-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const taskElement = e.target.closest('.task-item, .board-task');
                const taskId = taskElement.dataset.id;
                
                showConfirmModal('确认删除', '确定要删除这个任务吗？此操作不可撤销。', async () => {
                    try {
                        await API.tasks.delete(taskId);
                        // 从DOM和状态中移除任务
                        taskElement.remove();
                        state.tasks = state.tasks.filter(t => t.id !== taskId);
                        
                        // 如果没有任务了，重新渲染空状态
                        if (state.tasks.length === 0) {
                            renderTasks();
                        }
                        
                        showNotification('任务已删除', 'success');
                    } catch (error) {
                        console.error('删除任务失败:', error);
                        showNotification('删除任务失败', 'error');
                    }
                });
            });
        });
    }
    
    // 设置事件监听器
    function setupEventListeners() {
        // 任务添加表单
        if (taskForm) {
            taskForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const taskText = taskInput.value.trim();
                if (!taskText) return;
                
                try {
                    // 默认类别取决于当前筛选
                    const category = state.currentCategory || '其他';
                    
                    // 创建任务
                    const newTask = {
                        text: taskText,
                        category: category,
                        completed: false
                    };
                    
                    const response = await API.tasks.create(newTask);
                    
                    // 添加到任务列表并重新渲染
                    state.tasks.unshift(response);
                    sortTasks();
                    renderTasks();
                    
                    // 清空输入框
                    taskInput.value = '';
                    
                    showNotification('任务已添加', 'success');
                } catch (error) {
                    console.error('添加任务失败:', error);
                    showNotification('添加任务失败', 'error');
                }
            });
        }
        
        // 分类筛选
        document.querySelectorAll('.main-nav a[data-category]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // 更新当前类别
                state.currentCategory = e.target.dataset.category;
                state.currentFilter = null;
                
                // 更新标题
                currentViewTitle.textContent = `${state.currentCategory} 类别任务`;
                
                // 高亮当前选中的导航项
                document.querySelectorAll('.main-nav li').forEach(item => {
                    item.classList.remove('active');
                });
                e.target.closest('li').classList.add('active');
                
                // 重新加载任务
                loadTasks();
            });
        });
        
        // 过滤器
        document.querySelectorAll('.main-nav a[data-filter]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // 更新当前过滤器
                state.currentFilter = e.target.dataset.filter;
                state.currentCategory = null;
                
                // 更新标题
                if (state.currentFilter === 'today') {
                    currentViewTitle.textContent = '今天的任务';
                } else if (state.currentFilter === 'upcoming') {
                    currentViewTitle.textContent = '即将到期的任务';
                } else if (state.currentFilter === 'completed') {
                    currentViewTitle.textContent = '已完成的任务';
                } else if (state.currentFilter === 'incomplete') {
                    currentViewTitle.textContent = '未完成的任务';
                }
                
                // 高亮当前选中的导航项
                document.querySelectorAll('.main-nav li').forEach(item => {
                    item.classList.remove('active');
                });
                e.target.closest('li').classList.add('active');
                
                // 重新加载任务
                loadTasks();
            });
        });
        
        // 排序选择器
        const sortSelect = document.getElementById('sort-by');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                state.sortBy = sortSelect.value;
                sortTasks();
                renderTasks();
            });
        }
        
        // 视图切换
        document.querySelectorAll('.view-options button').forEach(btn => {
            btn.addEventListener('click', () => {
                const viewMode = btn.dataset.view;
                
                // 更新视图模式
                state.viewMode = viewMode;
                
                // 更新按钮状态
                document.querySelectorAll('.view-options button').forEach(b => {
                    b.classList.toggle('active', b.dataset.view === viewMode);
                });
                
                // 重新渲染
                renderTasks();
            });
        });
    }
    
    // 显示编辑任务模态框
    function showEditTaskModal(task) {
        const modalContainer = document.getElementById('modal-container');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        const modalFooter = document.getElementById('modal-footer');
        
        modalTitle.textContent = '编辑任务';
        
        // 构建表单
        modalBody.innerHTML = `
            <form id="edit-task-form" class="task-edit-form">
                <div class="form-group">
                    <label for="edit-task-text">任务内容</label>
                    <input type="text" id="edit-task-text" value="${task.text}" required>
                </div>
                <div class="form-group">
                    <label for="edit-task-category">类别</label>
                    <select id="edit-task-category">
                        <option value="工作" ${task.category === '工作' ? 'selected' : ''}>工作</option>
                        <option value="个人" ${task.category === '个人' ? 'selected' : ''}>个人</option>
                        <option value="学习" ${task.category === '学习' ? 'selected' : ''}>学习</option>
                        <option value="其他" ${task.category === '其他' ? 'selected' : ''}>其他</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-task-due-date">截止日期</label>
                    <input type="date" id="edit-task-due-date" value="${task.due_date || ''}">
                </div>
                <div class="form-group">
                    <label for="edit-task-due-time">截止时间</label>
                    <input type="time" id="edit-task-due-time" value="${task.due_time || ''}">
                </div>
                <div class="form-group">
                    <label for="edit-task-priority">优先级</label>
                    <select id="edit-task-priority">
                        <option value="高" ${task.priority === '高' ? 'selected' : ''}>高</option>
                        <option value="中" ${task.priority === '中' ? 'selected' : ''}>中</option>
                        <option value="正常" ${task.priority === '正常' ? 'selected' : ''}>正常</option>
                        <option value="低" ${task.priority === '低' ? 'selected' : ''}>低</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="checkbox">
                        <input type="checkbox" id="edit-task-completed" ${task.completed ? 'checked' : ''}>
                        <span>已完成</span>
                    </label>
                </div>
            </form>
        `;
        
        // 底部按钮
        modalFooter.innerHTML = `
            <button id="edit-task-cancel" class="btn btn-secondary">取消</button>
            <button id="edit-task-save" class="btn btn-primary">保存</button>
        `;
        
        // 显示模态框
        modalContainer.style.display = 'flex';
        
        // 绑定事件
        document.getElementById('modal-close').addEventListener('click', () => {
            modalContainer.style.display = 'none';
        });
        
        document.getElementById('edit-task-cancel').addEventListener('click', () => {
            modalContainer.style.display = 'none';
        });
        
        document.getElementById('edit-task-save').addEventListener('click', async () => {
            const updatedTask = {
                text: document.getElementById('edit-task-text').value,
                category: document.getElementById('edit-task-category').value,
                due_date: document.getElementById('edit-task-due-date').value || null,
                due_time: document.getElementById('edit-task-due-time').value || null,
                priority: document.getElementById('edit-task-priority').value,
                completed: document.getElementById('edit-task-completed').checked
            };
            
            try {
                await API.tasks.update(task.id, updatedTask);
                
                // 更新本地任务状态
                const taskIndex = state.tasks.findIndex(t => t.id === task.id);
                if (taskIndex !== -1) {
                    state.tasks[taskIndex] = { ...state.tasks[taskIndex], ...updatedTask };
                }
                
                // 重新渲染任务列表
                sortTasks();
                renderTasks();
                
                modalContainer.style.display = 'none';
                showNotification('任务已更新', 'success');
            } catch (error) {
                console.error('更新任务失败:', error);
                showNotification('更新任务失败', 'error');
            }
        });
    }
    
    // 显示确认模态框
    function showConfirmModal(title, message, onConfirm) {
        const modalContainer = document.getElementById('modal-container');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        const modalFooter = document.getElementById('modal-footer');
        
        modalTitle.textContent = title;
        modalBody.innerHTML = `<p>${message}</p>`;
        modalFooter.innerHTML = `
            <button id="confirm-cancel" class="btn btn-secondary">取消</button>
            <button id="confirm-ok" class="btn btn-danger">确定</button>
        `;
        
        // 显示模态框
        modalContainer.style.display = 'flex';
        
        // 绑定事件
        document.getElementById('modal-close').addEventListener('click', () => {
            modalContainer.style.display = 'none';
        });
        
        document.getElementById('confirm-cancel').addEventListener('click', () => {
            modalContainer.style.display = 'none';
        });
        
        document.getElementById('confirm-ok').addEventListener('click', () => {
            modalContainer.style.display = 'none';
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        });
    }
    
    // 显示通知
    function showNotification(message, type = 'info') {
        // 检查是否已存在通知容器
        let notificationContainer = document.querySelector('.notification-container');
        
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="bi ${getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close"><i class="bi bi-x"></i></button>
        `;
        
        // 添加到容器
        notificationContainer.appendChild(notification);
        
        // 自动关闭
        setTimeout(() => {
            notification.classList.add('hide');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
        
        // 关闭按钮
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('hide');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }
    
    // 辅助函数
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    }
    
    function getPriorityClass(priority) {
        switch (priority) {
            case '高': return 'priority-high';
            case '中': return 'priority-medium';
            case '低': return 'priority-low';
            default: return 'priority-normal';
        }
    }
    
    function getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'bi-check-circle';
            case 'error': return 'bi-exclamation-circle';
            case 'warning': return 'bi-exclamation-triangle';
            default: return 'bi-info-circle';
        }
    }
    
    // 初始化
    initTasks();
});