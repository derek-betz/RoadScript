"""Setup configuration for RoadScript."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="roadscript",
    version="1.0.0",
    author="INDOT Engineering Core Team",
    description="Deterministic Engineering Core for INDOT Roadway Design",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4==4.12.3",
        "fastapi==0.115.6",
        "pymupdf==1.23.26",
        "python-dotenv==1.0.1",
        "requests==2.32.3",
        "uvicorn[standard]==0.30.6",
    ],
    extras_require={
        "rag": [
            "chromadb==0.4.24",
            "httpx==0.27.2",
            "numpy==1.26.4",
            "openai==1.40.0",
            "sentence-transformers==2.7.0",
        ],
        "dev": [
            "pytest==7.4.4",
            "pytest-cov==4.1.0",
        ],
    },
    include_package_data=True,
)
