import os
import re
from collections import defaultdict


def get_migration_files():
    files = sorted([f for f in os.listdir("alembic/versions") if f.endswith(".py")])
    migrations = {}
    for f in files:
        with open(f"alembic/versions/{f}", "r") as file:
            content = file.read()
            rev = re.search(r"revision = ['\"](.+)['\"]", content)
            down_rev = re.search(r"down_revision = ['\"](.+)['\"]", content)

            if rev:
                rev_id = rev.group(1)
                down_rev_id = down_rev.group(1) if down_rev else None
                migrations[rev_id] = {"filename": f, "down_revision": down_rev_id}
    return migrations


def main():
    print("--- Migration Conflict Report ---")
    migrations = get_migration_files()
    down_revisions = defaultdict(list)

    for rev, data in migrations.items():
        down_revisions[data["down_revision"]].append(rev)

    conflicts = {
        dr: revs
        for dr, revs in down_revisions.items()
        if len(revs) > 1 and dr is not None
    }

    if conflicts:
        print("CONFLICTS DETECTED:")
        for dr, revs in conflicts.items():
            print(f"Down Revision {dr} is shared by multiple revisions:")
            for rev in revs:
                print(f"  - {migrations[rev]['filename']} (Revision: {rev})")
    else:
        print("No migration conflicts found based on down_revision.")


if __name__ == "__main__":
    main()
