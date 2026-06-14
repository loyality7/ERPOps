from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="erpops",
    version="0.0.1",
    description="ErpOps — Custom ERPNext application for Shopify integration and live operational feeds",
    author="Operator",
    author_email="operator@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
