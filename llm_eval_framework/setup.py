"""
Setup script for LLM Evaluation Framework.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="llm-eval-framework",
    version="0.2.0",
    author="LLM Evaluation Team",
    author_email="contact@llm-eval.dev",
    description="Universal LLM testing framework with multi-provider support via LiteLLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/llm-eval/llm-eval-framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "full": [
            "weasyprint>=60.0",
            "reportlab>=4.0.0", 
            "matplotlib>=3.7.0",
            "plotly>=5.0.0"
        ],
        "pdf": ["weasyprint>=60.0", "reportlab>=4.0.0"],
        "viz": ["matplotlib>=3.7.0", "plotly>=5.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "llm-eval=llm_eval.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "llm_eval": [
            "reporting/templates/*.html",
            "web/static/*",
            "web/templates/*.html"
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/llm-eval/llm-eval-framework/issues",
        "Source": "https://github.com/llm-eval/llm-eval-framework",
        "Documentation": "https://docs.llm-eval.dev",
    },
)