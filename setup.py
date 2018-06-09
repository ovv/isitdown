import pathlib
import setuptools

LONG_DESCRIPTION = pathlib.Path("README.rst").read_text("utf-8")

requires = {
    "install": ["attrs", "aiohttp", "asyncssh", "aiosmtplib"],
    "setup": ["pytest-runner"],
    "dev": [
        "tox",
        "black",
        "pytest",
        "coverage",
        "pytest-coverage",
        "pytest-asyncio",
        "sphinx",
        "sphinxcontrib-asyncio",
        "sphinxcontrib-napoleon",
    ],
}


def find_version():
    with open("isitdown/__version__.py") as f:
        version = f.readlines()[-1].split("=")[-1].strip().strip("'").strip('"')
        if not version:
            raise RuntimeError("No version found")

    return version


setuptools.setup(
    name="isitdown",
    long_description=LONG_DESCRIPTION,
    description="Dead simple status monitoring tool",
    keywords=[],
    packages=setuptools.find_packages(exclude=("tests",)),
    zip_safe=True,
    install_requires=requires["install"],
    setup_requires=requires["setup"],
    extras_require={"dev": requires["dev"]},
    # python_requires='>=3.6',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
    ],
    author="Ovv",
    author_email="contact@ovv.wtf",
    license="MIT",
    url="https://github.com/ovv/isitdown",
    version=find_version(),
)
