from setuptools import setup, find_packages

setup(
    name="repo-scrapper",
    version="1.0.0",
    description="AI-powered GitHub repository search & scraper CLI",
    packages=find_packages() or ["repo_scrapper_cli"],  # Fallback package name
    py_modules=[],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "repo-scrapper=repo_scrapper_cli.main:main",
        ],
    },
)