import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="pricing_calculator",
    version="0.0.1",
    description="Pricing Calculator for Frappe/ERPNext",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pricing Calculator Team",
    author_email="support@example.com",
    url="https://example.com/pricing-calculator",
    license="MIT",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["frappe"],
    python_requires=">=3.10",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Frappe",
        "Operating System :: OS Independent",
    ],
)


