"""Create or update all tables. Safe to run more than once.

The Streamlit app also does this automatically when it starts.
"""

from app.schema import ensure_schema

if __name__ == "__main__":
    ensure_schema()
    print("All tables are ready.")
