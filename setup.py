from setuptools import setup, find_packages

setup(
    name="quanthreum",
    version="1.0.0",
    description="Quanthreum (QTH) - NIST-Grade Post-Quantum Blockchain & Enterprise Security SDK",
    author="Quanthreum Team",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "quanthreum": ["bip39_words.txt"],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security :: Cryptography",
    ],
)
