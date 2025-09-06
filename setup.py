from setuptools import setup, find_packages

setup(
    name="firmaforge",
    version="0.1.0",
    description="Firmware modification and analysis tool",
    author="Nathan Leung",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pycryptodome>=3.15.0",
        "python-magic>=0.4.27",
        "hexdump>=3.3",
    ],
    entry_points={
        "console_scripts": [
            "firmaforge=firmaforge.cli:main",
        ],
    },
    python_requires=">=3.8",
)
