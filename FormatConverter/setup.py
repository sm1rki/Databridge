from setuptools import setup, find_packages

setup(
    name="databridge",
    version="1.0.0",
    description="DataBridge - универсальный конвертер и валидатор данных (CSV, JSON, XML, Excel)",
    author="DataBridge Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "openpyxl>=3.1.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "databridge=databridge.cli.main:main",
        ],
    },
)
