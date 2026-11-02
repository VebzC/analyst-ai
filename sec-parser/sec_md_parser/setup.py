from setuptools import setup, find_packages

setup(
    name="sec_md_parser",
    version="0.1.0",
    description="SEC Filing HTML/XBRL to Markdown Converter",
    author="Analyst AI",
    author_email="info@example.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.10.0",
        "lxml>=4.6.3",
        "requests>=2.26.0",
        "markdown>=3.3.4",
        "pydantic>=1.9.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "black>=21.9b0",
            "isort>=5.9.3",
            "mypy>=0.910",
            "flake8>=3.9.2",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
