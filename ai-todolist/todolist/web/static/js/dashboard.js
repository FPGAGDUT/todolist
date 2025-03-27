/**
 * AI TodoList 仪表盘主脚本
 * 负责处理任务数据展示、图表生成和页面交互
 */

// 全局变量存储任务数据
let allTasks = [];
let chartInstances = {};

// 在DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    if (!localStorage.getItem('auth_token')) {
        window.location.href = 'login.html';
        return;
    }
    
    // 显示用户名
    const username = localStorage.getItem('username');
    if (username) {
        document.getElementById('username').textContent = username;
    }
    
    // 初始化侧边栏
    initSidebar();
    
    // 加载任务数据
    loadTaskData();
    
    // 绑定刷新按钮事件
    document.getElementById('refresh-data').addEventListener('click', function() {
        loadTaskData(true);
    });
    
    // 绑定过滤和排序事件
    initFiltersAndSorting();
    
    // 绑定未来任务范围按钮
    const timeRangeButtons = document.querySelectorAll('.time-range-filter button');
    timeRangeButtons.forEach(button => {
        button.addEventListener('click', function() {
            timeRangeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            updateUpcomingTasks(this.dataset.range);
        });
    });
    
    // 绑定分析范围下拉菜单
    document.getElementById('analytics-range').addEventListener('change', function() {
        updateAnalyticsCharts(this.value);
    });
    
    // 设置今日日期
    updateTodayDate();
});

/**
 * 初始化侧边栏交互
 */
function initSidebar() {
    // 侧边栏切换按钮
    document.getElementById('sidebar-toggle').addEventListener('click', function() {
        document.querySelector('.app-container').classList.toggle('sidebar-collapsed');
    });
    
    // 导航链接
    const navLinks = document.querySelectorAll('.main-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 更新活动链接
            navLinks.forEach(l => l.parentElement.classList.remove('active'));
            this.parentElement.classList.add('active');
            
            // 获取视图ID
            if (this.dataset.view) {
                showView(this.dataset.view);
            } else if (this.dataset.category) {
                filterTasksByCategory(this.dataset.category);
            }
        });
    });
    
    // 退出按钮
    document.getElementById('logout-btn').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('username');
        window.location.href = 'login.html';
    });
    
    // 设置按钮
    document.getElementById('settings-btn').addEventListener('click', function(e) {
        e.preventDefault();
        // 打开设置模态框（在settings.js中处理）
        if (typeof openSettings === 'function') {
            openSettings();
        }
    });
}

/**
 * 显示指定视图
 */
function showView(viewId) {
    // 隐藏所有视图
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示选中的视图
    const targetView = document.getElementById(`${viewId}-view`);
    if (targetView) {
        targetView.classList.add('active');
        
        // 根据视图类型执行特定操作
        if (viewId === 'overview') {
            updateOverviewData();
        } else if (viewId === 'all-tasks') {
            renderAllTasks();
        } else if (viewId === 'today') {
            renderTodayTasks();
        } else if (viewId === 'upcoming') {
            updateUpcomingTasks('week'); // 默认显示本周
        } else if (viewId === 'analytics') {
            updateAnalyticsCharts(30); // 默认显示30天
        }
    }
}

/**
 * 加载任务数据
 */
function loadTaskData(showRefresh = false) {
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'global-loading';
    loadingIndicator.innerHTML = '<div class="spinner"></div><p>正在同步数据...</p>';
    
    if (showRefresh) {
        document.body.appendChild(loadingIndicator);
    }
    
    // 设置上次同步时间显示
    const now = new Date();
    const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                       now.getMinutes().toString().padStart(2, '0');
    document.getElementById('last-sync').textContent = `上次同步: ${timeString}`;
    document.getElementById('last-sync-time').textContent = timeString;
    
    // 加载任务数据
    API.tasks.getAll()
        .then(response => {
            allTasks = response.tasks || [];
            console.log('加载了', allTasks.length, '个任务');
            
            // 更新所有视图
            updateOverviewData();
            renderAllTasks();
            renderTodayTasks();
            updateUpcomingTasks('week');
            
            // 延迟一点移除加载指示器，提供更好的视觉反馈
            if (showRefresh) {
                setTimeout(() => {
                    loadingIndicator.remove();
                    showNotification('数据已更新', 'success');
                }, 500);
            }
        })
        .catch(error => {
            console.error('加载任务数据失败:', error);
            if (showRefresh) {
                loadingIndicator.remove();
                showNotification('更新数据失败，请重试', 'error');
            }
        });
}

/**
 * 更新今日日期显示
 */
function updateTodayDate() {
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
    const dateString = today.toLocaleDateString('zh-CN', options);
    document.getElementById('today-date').textContent = dateString;
}

/**
 * 更新概览数据
 */
function updateOverviewData() {
    // 获取日期
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - today.getDay());
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    const last7Days = new Date(today);
    last7Days.setDate(today.getDate() - 7);
    
    const last30Days = new Date(today);
    last30Days.setDate(today.getDate() - 30);
    
    // 过滤任务
    const todayTasks = allTasks.filter(task => {
        const dueDate = task.due_date ? new Date(task.due_date) : null;
        return dueDate && dueDate.toDateString() === today.toDateString() && !task.completed;
    });
    
    const weekTasks = allTasks.filter(task => {
        const dueDate = task.due_date ? new Date(task.due_date) : null;
        return dueDate && dueDate >= weekStart && dueDate <= weekEnd && !task.completed;
    });
    
    const completedRecent = allTasks.filter(task => {
        const completedDate = task.completed_at ? new Date(task.completed_at) : null;
        return task.completed && completedDate && completedDate >= last7Days;
    });
    
    // 计算完成率
    const last30DaysTasks = allTasks.filter(task => {
        const dueDate = task.due_date ? new Date(task.due_date) : null;
        return dueDate && dueDate >= last30Days && dueDate <= today;
    });
    
    const last30DaysCompleted = last30DaysTasks.filter(task => task.completed);
    const completionRate = last30DaysTasks.length > 0 
        ? Math.round((last30DaysCompleted.length / last30DaysTasks.length) * 100) 
        : 0;
    
    // 更新统计卡片
    document.querySelector('#today-count .stat-number').textContent = todayTasks.length;
    document.querySelector('#week-count .stat-number').textContent = weekTasks.length;
    document.querySelector('#completed-count .stat-number').textContent = completedRecent.length;
    document.querySelector('#completion-rate .stat-number').textContent = `${completionRate}%`;
    
    // 更新紧急任务列表
    const urgentTasks = allTasks.filter(task => {
        return task.priority === '高' && !task.completed;
    }).slice(0, 5); // 最多显示5个
    
    const urgentTaskList = document.getElementById('urgent-task-list');
    urgentTaskList.innerHTML = '';
    
    if (urgentTasks.length === 0) {
        urgentTaskList.innerHTML = '<li class="empty-message">当前没有紧急任务</li>';
    } else {
        urgentTasks.forEach(task => {
            const li = document.createElement('li');
            li.className = 'task-preview-item';
            
            const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString('zh-CN') : '无截止日期';
            const category = task.category || '其他';
            
            li.innerHTML = `
                <div class="task-preview-content">
                    <div class="task-preview-title">${task.text}</div>
                    <div class="task-preview-meta">
                        <span class="task-category">${category}</span>
                        <span class="task-due-date"><i class="bi bi-calendar"></i> ${dueDate}</span>
                    </div>
                </div>
                <div class="task-preview-actions">
                    <button class="btn-icon view-task" data-id="${task.id}"><i class="bi bi-eye"></i></button>
                </div>
            `;
            
            urgentTaskList.appendChild(li);
            
            // 添加任务详情查看事件
            li.querySelector('.view-task').addEventListener('click', function() {
                showTaskDetails(task.id);
            });
        });
    }
    
    // 更新今日任务列表
    const todayTaskList = document.getElementById('today-task-list');
    todayTaskList.innerHTML = '';
    
    if (todayTasks.length === 0) {
        todayTaskList.innerHTML = '<li class="empty-message">今天没有任务安排</li>';
    } else {
        const tasksToShow = todayTasks.slice(0, 5); // 最多显示5个
        tasksToShow.forEach(task => {
            const li = document.createElement('li');
            li.className = 'task-preview-item';
            
            const dueTime = task.due_time || '';
            const category = task.category || '其他';
            
            li.innerHTML = `
                <div class="task-preview-content">
                    <div class="task-preview-title">${task.text}</div>
                    <div class="task-preview-meta">
                        <span class="task-category">${category}</span>
                        ${dueTime ? `<span class="task-due-time"><i class="bi bi-clock"></i> ${dueTime}</span>` : ''}
                    </div>
                </div>
                <div class="task-preview-actions">
                    <button class="btn-icon view-task" data-id="${task.id}"><i class="bi bi-eye"></i></button>
                </div>
            `;
            
            todayTaskList.appendChild(li);
            
            // 添加任务详情查看事件
            li.querySelector('.view-task').addEventListener('click', function() {
                showTaskDetails(task.id);
            });
        });
    }
    
    // 更新图表
    updateWeeklyChart();
    updateCategoryChart();
}

/**
 * 更新每周任务完成图表
 */
function updateWeeklyChart() {
    const ctx = document.getElementById('weekly-chart').getContext('2d');
    
    // 准备图表数据
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // 获取过去7天的日期标签
    const dateLabels = [];
    const completedData = [];
    const addedData = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        
        // 添加日期标签 (周一, 周二 等)
        const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        dateLabels.push(weekdayNames[date.getDay()]);
        
        // 计算当天完成的任务
        const completedCount = allTasks.filter(task => {
            if (!task.completed || !task.completed_at) return false;
            const completedDate = new Date(task.completed_at);
            return completedDate.toDateString() === date.toDateString();
        }).length;
        
        // 计算当天添加的任务
        const addedCount = allTasks.filter(task => {
            if (!task.created_at) return false;
            const createdDate = new Date(task.created_at);
            return createdDate.toDateString() === date.toDateString();
        }).length;
        
        completedData.push(completedCount);
        addedData.push(addedCount);
    }
    
    // 销毁旧图表
    if (chartInstances.weekly) {
        chartInstances.weekly.destroy();
    }
    
    // 创建新图表
    chartInstances.weekly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dateLabels,
            datasets: [
                {
                    label: '已完成',
                    data: completedData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: '新添加',
                    data: addedData,
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

/**
 * 更新分类饼图
 */
function updateCategoryChart() {
    const ctx = document.getElementById('category-chart').getContext('2d');
    
    // 统计各分类的任务数量
    const categories = {};
    
    allTasks.forEach(task => {
        const category = task.category || '其他';
        if (!categories[category]) {
            categories[category] = 0;
        }
        categories[category]++;
    });
    
    // 准备饼图数据
    const labels = Object.keys(categories);
    const data = Object.values(categories);
    const backgroundColors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)'
    ];
    
    // 销毁旧图表
    if (chartInstances.category) {
        chartInstances.category.destroy();
    }
    
    // 创建新图表
    chartInstances.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderColor: 'white',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 渲染所有任务列表
 */
function renderAllTasks() {
    const taskList = document.getElementById('complete-task-list');
    const statusFilter = document.getElementById('status-filter').value;
    const sortBy = document.getElementById('sort-by').value;
    
    // 过滤任务
    let filteredTasks = [...allTasks];
    
    if (statusFilter === 'pending') {
        filteredTasks = filteredTasks.filter(task => !task.completed);
    } else if (statusFilter === 'completed') {
        filteredTasks = filteredTasks.filter(task => task.completed);
    }
    
    // 排序任务
    filteredTasks.sort((a, b) => {
        if (sortBy === 'date-asc') {
            return new Date(a.due_date || '9999-12-31') - new Date(b.due_date || '9999-12-31');
        } else if (sortBy === 'date-desc') {
            return new Date(b.due_date || '1970-01-01') - new Date(a.due_date || '1970-01-01');
        } else if (sortBy === 'priority') {
            const priorityOrder = { '高': 1, '正常': 2, '低': 3 };
            return (priorityOrder[a.priority] || 99) - (priorityOrder[b.priority] || 99);
        } else if (sortBy === 'category') {
            return (a.category || '其他').localeCompare(b.category || '其他');
        }
        return 0;
    });
    
    // 渲染任务列表
    taskList.innerHTML = '';
    
    if (filteredTasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <p>没有找到任务</p>
            </div>
        `;
        return;
    }
    
    filteredTasks.forEach(task => {
        const taskItem = createTaskElement(task);
        taskList.appendChild(taskItem);
    });
}

/**
 * 渲染今日任务列表
 */
function renderTodayTasks() {
    const taskList = document.getElementById('today-tasks-list');
    
    // 过滤今日任务
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const todayTasks = allTasks.filter(task => {
        if (!task.due_date) return false;
        const dueDate = new Date(task.due_date);
        return dueDate.toDateString() === today.toDateString();
    });
    
    // 渲染任务列表
    taskList.innerHTML = '';
    
    if (todayTasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-calendar-check"></i>
                <p>今天没有计划中的任务</p>
            </div>
        `;
        return;
    }
    
    // 首先显示未完成的任务
    const pendingTasks = todayTasks.filter(task => !task.completed);
    const completedTasks = todayTasks.filter(task => task.completed);
    
    if (pendingTasks.length > 0) {
        pendingTasks.forEach(task => {
            const taskItem = createTaskElement(task);
            taskList.appendChild(taskItem);
        });
    }
    
    // 然后显示已完成的任务
    if (completedTasks.length > 0) {
        const completedHeader = document.createElement('div');
        completedHeader.className = 'task-section-header';
        completedHeader.innerHTML = `
            <h4>已完成 (${completedTasks.length})</h4>
        `;
        taskList.appendChild(completedHeader);
        
        completedTasks.forEach(task => {
            const taskItem = createTaskElement(task);
            taskList.appendChild(taskItem);
        });
    }
}

/**
 * 创建任务列表项元素
 */
function createTaskElement(task) {
    const taskItem = document.createElement('div');
    taskItem.className = `task-item ${task.completed ? 'completed' : ''}`;
    taskItem.dataset.id = task.id;
    
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString('zh-CN') : '无截止日期';
    const dueTime = task.due_time || '';
    const priority = task.priority || '正常';
    const category = task.category || '其他';
    
    taskItem.innerHTML = `
        <div class="task-status">
            <span class="status-indicator ${task.completed ? 'completed' : 'pending'}"></span>
        </div>
        <div class="task-content">
            <div class="task-title">${task.text}</div>
            <div class="task-meta">
                <span class="task-category">${category}</span>
                <span class="task-priority priority-${priority.toLowerCase()}">${priority}</span>
                <span class="task-due-date"><i class="bi bi-calendar"></i> ${dueDate}</span>
                ${dueTime ? `<span class="task-due-time"><i class="bi bi-clock"></i> ${dueTime}</span>` : ''}
            </div>
        </div>
        <div class="task-actions">
            <button class="btn-icon view-task" title="查看详情" data-id="${task.id}">
                <i class="bi bi-info-circle"></i>
            </button>
        </div>
    `;
    
    // 绑定查看详情事件
    taskItem.querySelector('.view-task').addEventListener('click', function() {
        showTaskDetails(task.id);
    });
    
    return taskItem;
}

/**
 * 更新未来任务视图
 */
function updateUpcomingTasks(range) {
    const container = document.getElementById('upcoming-tasks-container');
    container.innerHTML = '';
    
    // 获取日期范围
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let endDate;
    if (range === 'week') {
        endDate = new Date(today);
        endDate.setDate(today.getDate() + 7);
    } else if (range === 'month') {
        endDate = new Date(today);
        endDate.setMonth(today.getMonth() + 1);
    } else {
        // 所有未来任务
        endDate = new Date('9999-12-31');
    }
    
    // 过滤未来任务
    const upcomingTasks = allTasks.filter(task => {
        if (!task.due_date) return false;
        const dueDate = new Date(task.due_date);
        return dueDate >= today && dueDate <= endDate && !task.completed;
    });
    
    if (upcomingTasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-calendar"></i>
                <p>未来${range === 'week' ? '一周' : (range === 'month' ? '一个月' : '')}没有计划中的任务</p>
            </div>
        `;
        return;
    }
    
    // 按日期分组任务
    const groupedTasks = {};
    upcomingTasks.forEach(task => {
        const dueDate = new Date(task.due_date);
        const dateKey = dueDate.toISOString().split('T')[0];
        
        if (!groupedTasks[dateKey]) {
            groupedTasks[dateKey] = [];
        }
        groupedTasks[dateKey].push(task);
    });
    
    // 按日期排序
    const sortedDates = Object.keys(groupedTasks).sort();
    
    // 渲染分组任务
    sortedDates.forEach(dateKey => {
        const date = new Date(dateKey);
        const dateString = formatDateWithWeekday(date);
        const isToday = date.toDateString() === today.toDateString();
        
        const dateGroup = document.createElement('div');
        dateGroup.className = 'date-group';
        
        dateGroup.innerHTML = `
            <div class="date-header ${isToday ? 'today' : ''}">
                <div class="date-indicator">
                    <span class="date-day">${date.getDate()}</span>
                    <span class="date-month">${getMonthAbbr(date.getMonth())}</span>
                </div>
                <h3>${isToday ? '今天' : dateString}</h3>
                <span class="task-count">${groupedTasks[dateKey].length}个任务</span>
            </div>
            <div class="date-tasks"></div>
        `;
        
        const tasksContainer = dateGroup.querySelector('.date-tasks');
        groupedTasks[dateKey].forEach(task => {
            const taskItem = createTaskElement(task);
            tasksContainer.appendChild(taskItem);
        });
        
        container.appendChild(dateGroup);
    });
    
    // 生成简单日历视图
    generateCalendarView(sortedDates);
}

/**
 * 格式化日期，包含星期几
 */
function formatDateWithWeekday(date) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[date.getDay()];
    const month = date.getMonth() + 1;
    const day = date.getDate();
    
    return `${month}月${day}日 ${weekday}`;
}

/**
 * 获取月份缩写
 */
function getMonthAbbr(monthIndex) {
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    return months[monthIndex];
}

/**
 * 生成简单日历视图
 */
function generateCalendarView(taskDates) {
    const calendar = document.getElementById('task-calendar');
    calendar.innerHTML = '';
    
    // 获取当前月份的所有日期
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // 获取当前月份的第一天和最后一天
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    
    // 创建日历头部
    const calendarHeader = document.createElement('div');
    calendarHeader.className = 'calendar-header';
    calendarHeader.innerHTML = `
        <h3>${currentYear}年${currentMonth + 1}月</h3>
    `;
    calendar.appendChild(calendarHeader);
    
    // 创建星期栏
    const weekdayRow = document.createElement('div');
    weekdayRow.className = 'calendar-weekdays';
    
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    weekdays.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-weekday';
        dayElement.textContent = day;
        weekdayRow.appendChild(dayElement);
    });
    
    calendar.appendChild(weekdayRow);
    
    // 创建日期网格
    const daysGrid = document.createElement('div');
    daysGrid.className = 'calendar-days';
    
    // 添加每月第一天之前的空白
    for (let i = 0; i < firstDay.getDay(); i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        daysGrid.appendChild(emptyDay);
    }
    
    // 添加月份中的每一天
    for (let i = 1; i <= lastDay.getDate(); i++) {
        const dayElement = document.createElement('div');
        const currentDate = new Date(currentYear, currentMonth, i);
        const dateString = currentDate.toISOString().split('T')[0];
        
        // 检查是否有任务在这一天
        const hasTask = taskDates.includes(dateString);
        
        // 检查是否是今天
        const isToday = currentDate.toDateString() === today.toDateString();
        
        dayElement.className = `calendar-day ${isToday ? 'today' : ''} ${hasTask ? 'has-task' : ''}`;
        
        dayElement.innerHTML = `
            <span class="day-number">${i}</span>
            ${hasTask ? '<span class="task-indicator"></span>' : ''}
        `;
        
        daysGrid.appendChild(dayElement);
    }
    
    calendar.appendChild(daysGrid);
}

/**
 * 更新分析视图图表
 */
function updateAnalyticsCharts(days) {
    // 准备数据
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(days));
    
    // 更新完成率趋势图
    updateCompletionTrendChart(startDate, endDate);
    
    // 更新分类饼图
    updateCategoryPieChart();
    
    // 更新每日高效时段图
    updateProductivityChart();
    
    // 更新任务统计表格
    updateTaskStatsTable();
    
    // 更新生产力洞察
    updateProductivityInsights();
}

/**
 * 显示任务详情
 */
function showTaskDetails(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    
    const detailsPanel = document.getElementById('task-details');
    const panelContent = detailsPanel.querySelector('.panel-content');
    
    panelContent.innerHTML = `
        <div class="task-details-content">
            <div class="detail-group">
                <label>任务内容</label>
                <div class="detail-value task-text">${task.text}</div>
            </div>
            
            <div class="detail-group">
                <label>状态</label>
                <div class="detail-value">
                    <span class="status-badge ${task.completed ? 'completed' : 'pending'}">
                        ${task.completed ? '已完成' : '待处理'}
                    </span>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="detail-group">
                    <label>类别</label>
                    <div class="detail-value">
                        <span class="task-category">${task.category || '其他'}</span>
                    </div>
                </div>
                
                <div class="detail-group">
                    <label>优先级</label>
                    <div class="detail-value">
                        <span class="task-priority priority-${(task.priority || '正常').toLowerCase()}">
                            ${task.priority || '正常'}
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="detail-group">
                    <label>截止日期</label>
                    <div class="detail-value">
                        ${task.due_date ? new Date(task.due_date).toLocaleDateString('zh-CN') : '无截止日期'}
                    </div>
                </div>
                
                <div class="detail-group">
                    <label>截止时间</label>
                    <div class="detail-value">
                        ${task.due_time || '无具体时间'}
                    </div>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="detail-group">
                    <label>创建时间</label>
                    <div class="detail-value">
                        ${task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '未知'}
                    </div>
                </div>
                
                <div class="detail-group">
                    <label>完成时间</label>
                    <div class="detail-value">
                        ${task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '未完成'}
                    </div>
                </div>
            </div>
            
            ${task.notes ? `
                <div class="detail-group">
                    <label>备注</label>
                    <div class="detail-value task-notes">${task.notes}</div>
                </div>
            ` : ''}
        </div>
    `;
    
    // 显示面板
    detailsPanel.classList.add('visible');
    
    // 绑定关闭按钮
    document.getElementById('close-details').addEventListener('click', function() {
        detailsPanel.classList.remove('visible');
    });
}

/**
 * 初始化过滤和排序控件
 */
function initFiltersAndSorting() {
    const statusFilter = document.getElementById('status-filter');
    const sortBy = document.getElementById('sort-by');
    
    statusFilter.addEventListener('change', renderAllTasks);
    sortBy.addEventListener('change', renderAllTasks);
}

/**
 * 根据分类过滤任务
 */
function filterTasksByCategory(category) {
    // 切换到所有任务视图
    showView('all-tasks');
    
    // 手动过滤DOM元素
    const taskItems = document.querySelectorAll('.task-item');
    taskItems.forEach(item => {
        const taskCategory = item.querySelector('.task-category').textContent;
        if (category && taskCategory !== category) {
            item.style.display = 'none';
        } else {
            item.style.display = '';
        }
    });
    
    // 更新标题
    document.querySelector('#all-tasks-view .content-header h2').textContent = 
        category ? `${category}类任务` : '所有任务';
}

/**
 * 显示通知消息
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="bi ${getNotificationIcon(type)}"></i>
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

/**
 * 获取通知图标类名
 */
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'bi-check-circle';
        case 'error': return 'bi-exclamation-circle';
        case 'warning': return 'bi-exclamation-triangle';
        default: return 'bi-info-circle';
    }
}

// 分析图表相关函数 - 简化版本
function updateCompletionTrendChart(startDate, endDate) {
    // 简单模拟数据
    const ctx = document.getElementById('completion-trend-chart').getContext('2d');
    
    // 销毁旧图表
    if (chartInstances.completionTrend) {
        chartInstances.completionTrend.destroy();
    }
    
    // 生成日期标签
    const labels = [];
    const data = [];
    
    // 每7天一个数据点
    const daySpan = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24 * 7));
    
    for (let i = 0; i < 7; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i * daySpan);
        labels.push(date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }));
        
        // 模拟完成率数据
        data.push(Math.floor(Math.random() * 30) + 70); // 70-100%范围的随机值
    }
    
    // 创建图表
    chartInstances.completionTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '任务完成率',
                data: data,
                fill: true,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    min: 50,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `完成率: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

function updateCategoryPieChart() {
    // 使用与概览页面相同的分类饼图逻辑
    const ctx = document.getElementById('category-pie-chart').getContext('2d');
    
    // 统计各分类的任务数量
    const categories = {};
    
    allTasks.forEach(task => {
        const category = task.category || '其他';
        if (!categories[category]) {
            categories[category] = 0;
        }
        categories[category]++;
    });
    
    // 准备饼图数据
    const labels = Object.keys(categories);
    const data = Object.values(categories);
    const backgroundColors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)'
    ];
    
    // 销毁旧图表
    if (chartInstances.categoryPie) {
        chartInstances.categoryPie.destroy();
    }
    
    // 创建新图表
    chartInstances.categoryPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderColor: 'white',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

function updateProductivityChart() {
    // 模拟生产力时段数据
    const ctx = document.getElementById('productivity-chart').getContext('2d');
    
    // 销毁旧图表
    if (chartInstances.productivity) {
        chartInstances.productivity.destroy();
    }
    
    // 创建新图表
    chartInstances.productivity = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['上午', '中午', '下午', '晚上'],
            datasets: [{
                label: '任务完成数',
                data: [8, 3, 7, 5],
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 2
                    }
                }
            }
        }
    });
}

function updateTaskStatsTable() {
    // 模拟统计数据
    const statsTable = document.getElementById('stats-table-body');
    statsTable.innerHTML = '';
    
    // 获取所有类别
    const categories = {};
    allTasks.forEach(task => {
        const category = task.category || '其他';
        if (!categories[category]) {
            categories[category] = {
                pending: 0,
                completed: 0,
                avgTime: 0
            };
        }
        
        if (task.completed) {
            categories[category].completed++;
        } else {
            categories[category].pending++;
        }
    });
    
    // 生成表格行
    Object.entries(categories).forEach(([category, stats]) => {
        const total = stats.pending + stats.completed;
        const completionRate = total > 0 ? Math.round((stats.completed / total) * 100) : 0;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${category}</td>
            <td>${stats.pending}</td>
            <td>${stats.completed}</td>
            <td>${completionRate}%</td>
            <td>${(Math.random() * 3 + 1).toFixed(1)}</td>
        `;
        
        statsTable.appendChild(row);
    });
}

function updateProductivityInsights() {
    // 模拟生产力洞察
    const insightsContainer = document.getElementById('productivity-insights');
    insightsContainer.innerHTML = '';
    
    const insights = [
        {
            title: '高效时段',
            text: '您在上午完成的任务数量最多，建议将重要任务安排在上午。'
        },
        {
            title: '任务完成趋势',
            text: '您的任务完成率在过去30天呈上升趋势，保持这种良好习惯！'
        },
        {
            title: '类别平衡',
            text: '工作类型任务占比过高(68%)，建议平衡各类别任务分配。'
        }
    ];
    
    insights.forEach(insight => {
        const insightItem = document.createElement('div');
        insightItem.className = 'insight-item';
        insightItem.innerHTML = `
            <h4>${insight.title}</h4>
            <p>${insight.text}</p>
        `;
        insightsContainer.appendChild(insightItem);
    });
}