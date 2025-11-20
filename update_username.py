#!/usr/bin/env python3
"""
Quick script to replace YOUR_USERNAME with actual GitHub username
Usage: python update_username.py your_github_username
"""
import sys
from pathlib import Path

def update_username(username: str):
    """Replace YOUR_USERNAME with actual username in all relevant files."""

    files_to_update = [
        "README.md",
        "CONTRIBUTING.md",
        "GITHUB_SETUP.md",
        "pyproject.toml",
        "SECURITY.md",
        "SETUP_SUMMARY.md",
        "CHECKLIST.md"
    ]

    project_root = Path(__file__).parent
    updated_count = 0

    for filename in files_to_update:
        filepath = project_root / filename

        if not filepath.exists():
            print(f"⚠️  Skipping {filename} (not found)")
            continue

        try:
            content = filepath.read_text(encoding='utf-8')

            if "YOUR_USERNAME" in content:
                new_content = content.replace("YOUR_USERNAME", username)
                filepath.write_text(new_content, encoding='utf-8')
                updated_count += 1
                print(f"✅ Updated {filename}")
            else:
                print(f"ℹ️  No changes needed in {filename}")

        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")

    print(f"\n🎉 Updated {updated_count} file(s) with username: {username}")
    print("\n📝 Don't forget to also update:")
    print("   - your.email@example.com → your actual email")
    print("   - Your Name → your actual name")
    print("\n💡 Tip: Search for these strings manually to verify all are updated.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_username.py your_github_username")
        print("\nExample:")
        print("  python update_username.py adrpur")
        sys.exit(1)

    username = sys.argv[1]

    # Basic validation
    if not username or len(username) < 1:
        print("❌ Invalid username")
        sys.exit(1)

    print(f"🔄 Updating YOUR_USERNAME → {username}")
    print("=" * 60)

    update_username(username)

if __name__ == "__main__":
    main()

