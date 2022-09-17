#!/usr/bin/env python3
#
# aiojobs documentation build configuration file, created by
# sphinx-quickstart on Sat Jul  1 15:24:45 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import codecs
import os
import re
from typing import Dict

_docs_path = os.path.dirname(__file__)
_version_path = os.path.abspath(
    os.path.join(_docs_path, "..", "aiojobs", "__init__.py")
)
_version_info = None
with codecs.open(_version_path, "r", "latin1") as fp:
    try:
        match = re.search(
            r'^__version__ = "'
            r"(?P<major>\d+)"
            r"\.(?P<minor>\d+)"
            r"\.(?P<patch>\d+)"
            r'(?P<tag>.*)?"$',
            fp.read(),
            re.M,
        )
        if match is not None:
            _version_info = match.groupdict()
    except IndexError:
        pass

if _version_info is None:
    raise RuntimeError("Unable to determine version.")


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "alabaster",
    "sphinxcontrib.asyncio",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "aiojobs"
copyright = "2017, Andrew Svetlov"
author = "Andrew Svetlov"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "{major}.{minor}".format(**_version_info)
# The full version, including alpha/beta/rc tags.
release = "{major}.{minor}.{patch}-{tag}".format(**_version_info)

# The default language to highlight source code in.
highlight_language = "python3"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "logo": "aiojobs-icon-128x128.png",
    "description": "Jobs scheduler for managing asyncio background tasks",
    "github_user": "aio-libs",
    "github_repo": "aiojobs",
    "github_button": True,
    "github_type": "star",
    "github_banner": True,
    "travis_button": True,
    "codecov_button": True,
    "pre_bg": "#FFF6E5",
    "note_bg": "#E5ECD1",
    "note_border": "#BFCF8C",
    "body_text": "#482C0A",
    "sidebar_text": "#49443E",
    "sidebar_header": "#4B4032",
}

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "aiojobs-icon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "searchbox.html",
    ]
}


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "aiojobsdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements: Dict[str, str] = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, "aiojobs.tex", "aiojobs Documentation", "Andrew Svetlov", "manual"),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "aiojobs", "aiojobs Documentation", [author], 1)]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "aiojobs",
        "aiojobs Documentation",
        author,
        "aiojobs",
        "One line description of project.",
        "Miscellaneous",
    ),
]


# Example configuration for intersphinx:
# refer to the Python standard library.
intersphinx_mapping = {
    "https://docs.python.org/3": None,
    "aiohttp": ("https://aiohttp.readthedocs.io/en/stable/", None),
}
