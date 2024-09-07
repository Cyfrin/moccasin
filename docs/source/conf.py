# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import gaboon
import os
import sys

sys.path.insert(0, os.path.abspath("."))

project = "gaboon"
copyright = "2024, Patrick Collins, Charles Cooper"
author = "Patrick Collins, Charles Cooper"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinxarg.ext",
    "sphinx_copybutton",
    "sphinx_multiversion",
    "sphinxarg.ext",
]

master_doc = "toctree"
templates_path = ["_templates"]
exclude_patterns = [".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_theme_options = {
    "accent_color": "purple",
    "twitter_creator": "cyfrinaudits",
    "twitter_site": "cyfrinaudits",
    "twitter_url": "https://twitter.com/cyfrinaudits",
    "github_url": "https://github.com/cyfrin",
}
html_static_path = ["_static"]

# For the "Edit this page ->" link
html_context = {
    "source_type": "github",
    "source_user": "vyperlang",
    "source_repo": "gaboon",
}

# Options for sphinx_multiversion
smv_remote_whitelist = r"^origin$"
smv_branch_whitelist = r"^master$"  # master is gross
smv_tag_whitelist = r"^v\d+\.\d+.\d+$"
version = gaboon.version()  # TODO
