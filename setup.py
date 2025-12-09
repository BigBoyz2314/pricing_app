import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="pricing_calculator",
    version="0.0.1",
    description="Pricing Calculator for Frappe/ERPNext",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
)


