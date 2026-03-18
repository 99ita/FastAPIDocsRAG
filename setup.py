"""
Setup script for FastAPI Documentation RAG.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="FastAPI-Docs-RAG",
    version="0.1.0",
    author="FastAPI Docs RAG Team",
    author_email="team@fastapidocsrag.com",
    description="Enhanced RAG pipeline for FastAPI documentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/FastAPI-Docs-RAG",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Documentation",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langchain-core",
        "langchain-community",
        "langchain-text-splitters",
        "PyYAML",
        "sentence-transformers",
        "fastapi",
        "uvicorn",
        "streamlit",
        "google-cloud-storage",
        "vertexai",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
        "cloud": [
            "google-cloud-storage",
            "vertexai",
        ],
    },
    entry_points={
        "console_scripts": [
            "fastapi-docs-rag-ingest=scripts.ingest:main",
            "fastapi-docs-rag-serve=scripts.serve:main",
            "fastapi-docs-rag-embed=scripts.embed:main",
        ],
    },
)
