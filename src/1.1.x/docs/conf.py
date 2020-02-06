from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "itsdangerous"
copyright = "2011 Pallets Team"
author = "Pallets Team"
release, version = get_version("itsdangerous")

# General --------------------------------------------------------------

master_doc = "index"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "pallets_sphinx_themes"]
intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}

# HTML -----------------------------------------------------------------

html_theme = "flask"
html_theme_options = {"index_sidebar_logo": False}
html_context = {
    "project_links": [
        ProjectLink("Pallets에 후원하기", "https://palletsprojects.com/donate"),
        ProjectLink("웹사이트", "https://palletsprojects.com/p/itsdangerous/"),
        ProjectLink("PyPI 릴리스", "https://pypi.org/project/itsdangerous/"),
        ProjectLink("소스 코드", "https://github.com/pallets/itsdangerous/"),
        ProjectLink("이슈 트래커", "https://github.com/pallets/itsdangerous/issues/"),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_static_path = ["_static"]
html_logo = "_static/itsdangerous-logo-sidebar.png"
html_title = "itsdangerous Documentation ({})".format(version)
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, "itsdangerous-{}.tex".format(version), html_title, author, "manual")
]
