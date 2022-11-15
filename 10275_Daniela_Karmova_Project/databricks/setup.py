import io
import os

from setuptools import find_packages, setup

# read module requirements from requirements.txt instead of repeating the dependencies here:
with open("requirements.txt") as f:
    requirements = f.read().splitlines()
    install_requires = [r for r in requirements if not r == ""]

setup(
    name="uapc_aiacad",
    version=os.environ.get("ARTIFACT_LABEL_PEP440", "0.0.0+dev0"),
    author="SIT AI UAPC Team",
    author_email="uapc@mail.schwarz",
    description="Template project for UAPC",
    long_description=io.open("README.md", encoding="utf-8").read(),
    url="https://dev.azure.com/schwarzit/schwarzit.uapc-aiacad/_git/10275_Daniela_Karmova_Project",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires='>=3.8',
)

#https://schwarzit@dev.azure.com/schwarzit/schwarzit.uapc-tpl/_git/schwarzit.uapc-tpl
