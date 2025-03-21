from setuptools import setup, find_packages

setup(
    name="flashka",
    version="0.1.0",
    description="Flashka - Real Price Scanner & Shopping List App",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.0.0",
        "pytesseract",
        "Pillow",
        "pyzbar",
        "requests"
