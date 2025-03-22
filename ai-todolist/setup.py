from setuptools import setup, find_packages

setup(
    name='todolist',
    version='0.1.0',
    author='Chenhaha',
    author_email='your.email@example.com',
    description='A personal todo list application with AI integration for reminders and summaries.',
    packages=find_packages(),
    package_dir={
        'todolist': 'todolist',
        # 'todolist.desktop': 'todolist/desktop',
        # 'todolist.server': 'todolist/server',
        # 'todolist.ai': 'todolist/ai',
    },
    include_package_data=True,
    install_requires=[
        'flask',  # For the web application
        'requests',  # For making API calls
        'sqlalchemy',  # For database operations
        'pillow',  # For handling images (if needed for tray icon)
        'PyQt5',  # 添加PyQt5依赖
        # Add other dependencies as needed
    ],
    entry_points={
        'console_scripts': [
            'todolist-desktop=todolist.desktop.app:main',  # 修改入口点为toollist.desktop.app
            'todolist-server=todolist.server.main:main',  # 修改入口点为toollist.server.app
        ],
    },
    # entry_points={
    #     'gui_scripts': [  # 修改这里，从 console_scripts 改为 gui_scripts
    #         'todolist-desktop=todolist.desktop.app:main',
    #         # 'todolist-server=todolist.server.app:main',  # 服务器应保持 console_scripts
    #     ],
    #     'console_scripts': [
    #         'todolist-server=todolist.server.main:main',  # 服务器保持命令行方式
    #     ],
    # },
)

# from setuptools import setup, find_packages

# setup(
#     name='todolist',  # 可考虑改为 'ai-todolist' 以匹配项目目录
#     version='0.1.0',
#     author='Chenhaha',
#     author_email='your.email@example.com',
#     description='A personal todo list application with AI integration for reminders and summaries.',
#     packages=find_packages(where='todolist'),  # 自动查找 src 下的所有子包
#     package_dir={'': 'todolist'},  # 所有包位于 src 目录
#     include_package_data=True,  # 包含 MANIFEST.in 中指定的非 Python 文件
#     install_requires=[
#         'flask',        # 用于服务器端 Web 应用
#         'requests',     # 用于 API 调用
#         'sqlalchemy',   # 用于数据库操作
#         'pillow',       # 用于处理图像（如托盘图标）
#         'PyQt5',        # 用于桌面应用
#         # 如果有其他依赖，请在此添加
#     ],
#     entry_points={
#         'console_scripts': [
#             'todolist-desktop=todolist.desktop.app:main',  # 桌面应用入口
#             'todolist-server=todolist.server.app:main',    # 服务器端入口
#         ],
#     },
# )