"""
py2app setup script for building Recall.app
"""

from setuptools import setup, find_packages
from pathlib import Path

# App configuration
APP = ['app/menu_bar.py']
APP_NAME = "Recall"
BUNDLE_ID = "com.recall.memory"
VERSION = "1.0.0"

# Data files to include
DATA_FILES = [
    'resources',
    'README.md',
    'requirements.txt'
]

# py2app options
OPTIONS = {
    'argv_emulation': False,  # Don't emulate command line
    'strip': True,  # Strip debug symbols
    'iconfile': 'resources/icon.icns',  # App icon (if available)
    'plist': {
        # Bundle information
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': 'Recall Memory System',
        'CFBundleIdentifier': BUNDLE_ID,
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'CFBundleGetInfoString': f'Recall {VERSION} - Personal Memory Search',
        'NSHumanReadableCopyright': '© 2025 Recall Memory System',
        
        # Application behavior
        'LSUIElement': True,  # Hide from dock (menu bar only)
        'LSMinimumSystemVersion': '11.0',  # Require macOS Big Sur or later
        'NSSupportsAutomaticGraphicsSwitching': True,
        'NSHighResolutionCapable': True,  # Support Retina displays
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        
        # Permissions
        'NSAppleEventsUsageDescription': 'Recall needs AppleEvents to access WindRecorder data',
        'NSSystemAdministrationUsageDescription': 'Recall needs admin access for system monitoring',
        
        # URL schemes (for future use)
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'Recall Search',
                'CFBundleURLSchemes': ['recall']
            }
        ],
        
        # Document types
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Recall Archive',
                'CFBundleTypeExtensions': ['recall'],
                'CFBundleTypeRole': 'Viewer'
            }
        ]
    },
    
    # Include packages
    'packages': [
        'rumps',
        'chromadb', 
        'sentence_transformers',
        'paramiko',
        'pandas',
        'pydantic',
        'schedule',
        'logging',
        'json',
        'sqlite3',
        'pathlib',
        'threading',
        'datetime'
    ],
    
    # Include specific modules
    'includes': [
        'sqlite3',
        'json',
        'threading',
        'schedule',
        'logging',
        'datetime',
        'pathlib',
        'ssl',  # For HTTPS requests
        'socket',  # For network operations
        'subprocess',  # For system calls
        'os',
        'sys',
        'tempfile',
        'shutil',
        'gzip',
        'io'
    ],
    
    # Exclude unnecessary packages to reduce size
    'excludes': [
        'tkinter',
        'test',
        'tests',
        'unittest',
        'pdb',
        'doctest',
        'difflib',
        'inspect',
        'pydoc',
        'pygame',
        'matplotlib',
        'scipy',
        'numpy.f2py',
        'numpy.distutils',
        'IPython',
        'jupyter'
    ],
    
    # Resources
    'resources': [
        'core',
        'app'
    ],
    
    # Semi-standalone mode (include Python runtime)
    'semi_standalone': True,
    
    # Optimize bytecode
    'optimize': 2
}

# Additional setup for dependencies that might need special handling
SETUP_REQUIRES = [
    'py2app',
    'wheel'
]

INSTALL_REQUIRES = [
    'rumps>=0.4.0',
    'chromadb>=0.4.0',
    'sentence-transformers>=2.0.0',
    'paramiko>=3.0.0',
    'pandas>=2.0.0',
    'pydantic>=2.0.0',
    'schedule>=1.2.0',
    'python-dotenv>=1.0.0',
    'pillow>=10.0.0',
    'requests>=2.28.0'
]

# PyQt6 is optional (for GUI windows)
try:
    import PyQt6
    INSTALL_REQUIRES.append('PyQt6>=6.4.0')
    OPTIONS['packages'].append('PyQt6')
except ImportError:
    print("PyQt6 not found - GUI windows will not be available")

setup(
    name=APP_NAME,
    version=VERSION,
    description="Personal Memory Search System for macOS",
    long_description=open('README.md').read() if Path('README.md').exists() else "",
    long_description_content_type="text/markdown",
    author="Recall Team",
    author_email="info@recall.ai",
    url="https://github.com/recall/recall-app",
    
    # Python requirements
    python_requires='>=3.9',
    
    # Package discovery
    packages=find_packages(),
    package_data={
        'core': ['*.py'],
        'app': ['*.py'],
    },
    
    # Dependencies
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    
    # py2app configuration
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    
    # Entry points
    entry_points={
        'console_scripts': [
            'recall=app.menu_bar:main',
        ],
    },
    
    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Desktop Environment',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: System :: Monitoring'
    ],
    
    # Keywords
    keywords="memory search timeline macos windrecorder claude ai",
    
    # License
    license="MIT",
    
    # Include package data
    include_package_data=True,
    zip_safe=False
)