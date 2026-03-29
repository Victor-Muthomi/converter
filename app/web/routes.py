"""
Web blueprint — serves the frontend UI and static assets.
"""

from flask import Blueprint, render_template

web = Blueprint(
    "web",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


@web.route("/")
def index():
    """Render the main DocForge converter page."""
    return render_template("index.html")
