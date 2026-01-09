from setuptools import setup, find_packages

setup(
    name="options-trading-strategy",
    version="1.0.0",
    description="Automated options trading strategy for NVDA/GOOGL/TSLA/QQQ",
    author="AI Assistant",
    packages=find_packages(),
    install_requires=[
        "yfinance>=0.2.18",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
        "scipy>=1.7.0",
        "python-dateutil>=2.8.2",
        "requests>=2.26.0"
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "options-backtester=main:run_strategy",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)