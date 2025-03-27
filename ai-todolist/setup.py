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
        'jieba',
        'openai',
        # Add other dependencies as needed
    ],
    entry_points={
        'console_scripts': [
            'todolist-desktop=todolist.desktop.app:main',  # 修改入口点为toollist.desktop.app
            'todolist-server=todolist.server.main:main',  # 修改入口点为toollist.server.app
        ],
    },
)