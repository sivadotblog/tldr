"""
MkDocs Macros module for generating dynamic newsletter indexes.
"""

import os
import re
from pathlib import Path
from datetime import datetime


def define_env(env):
    """
    Define custom macros for MkDocs.
    """

    @env.macro
    def recent_newsletters(category, count=10):
        """
        Generate a list of the most recent newsletter links for a category.

        Args:
            category: The newsletter category (ai, data, devops, tech)
            count: Number of recent newsletters to show (default: 10)

        Returns:
            Markdown formatted list of recent newsletters
        """
        # Get the docs directory path
        docs_dir = Path(env.conf["docs_dir"])
        category_dir = docs_dir / category

        if not category_dir.exists():
            return f"*Category '{category}' not found.*"

        # Find all .md files except index.md
        newsletter_files = []
        for md_file in category_dir.glob("*.md"):
            if md_file.name != "index.md":
                # Extract date from filename (YYYY-MM-DD.md format)
                match = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", md_file.name)
                if match:
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        newsletter_files.append(
                            {
                                "filename": md_file.name,
                                "date": date_obj,
                                "date_str": date_str,
                                "path": md_file,
                            }
                        )
                    except ValueError:
                        continue

        # Sort by date (newest first)
        newsletter_files.sort(key=lambda x: x["date"], reverse=True)

        # Take only the requested count
        recent = newsletter_files[:count]

        if not recent:
            return "*No newsletters found.*"

        # Generate markdown list
        lines = ["## Latest Issues\n"]
        for item in recent:
            # Try to extract title from the first line of the file
            title = extract_title(item["path"])

            # Format: [Date - Title](filename)
            if title:
                lines.append(f"- [{item['date_str']}]({item['filename']}) - {title}")
            else:
                lines.append(f"- [{item['date_str']}]({item['filename']})")

        # Add link to browse all
        lines.append("\n---")
        lines.append(
            "\n*Use the sidebar to browse all newsletters or search above to find specific topics.*"
        )

        return "\n".join(lines)


def extract_title(file_path):
    """
    Extract the title from a markdown file.
    Looks for the first H1 heading or uses the first line.

    Args:
        file_path: Path to the markdown file

    Returns:
        Extracted title or None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Check for H1 heading
                if line.startswith("# "):
                    title = line[2:].strip()
                    # Remove any "TLDR AI" or "TLDR" prefixes
                    title = re.sub(
                        r"^TLDR\s+(AI|Data|DevOps|Tech)\s+\d{4}-\d{2}-\d{2}\s*",
                        "",
                        title,
                    )
                    # Clean up the title
                    title = title.strip()
                    if title and len(title) > 10:  # Make sure it's substantive
                        return title[:100]  # Truncate if too long

                # If no H1, look for text content (skip links and empty lines)
                if (
                    not line.startswith("[")
                    and not line.startswith("#")
                    and len(line) > 20
                ):
                    # Clean up and truncate
                    title = re.sub(r"\s+", " ", line)
                    return title[:100]

        return None
    except Exception:
        return None
