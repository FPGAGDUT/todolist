from setuptools import setup, find_packages

setup(
    name='ai-todolist',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A personal todo list application with AI integration for reminders and summaries.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'flask',  # For the web application
        'requests',  # For making API calls
        'sqlalchemy',  # For database operations
        'pillow',  # For handling images (if needed for tray icon)
        # Add other dependencies as needed
    ],
    entry_points={
        'console_scripts': [
            'ai-todolist-desktop=desktop.app:main',  # Entry point for desktop app
            'ai-todolist-web=web.app:main',  # Entry point for web app
        ],
    },
)