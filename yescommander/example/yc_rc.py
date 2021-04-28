from typing import List

import yescommander as yc

commanders: List[yc.BaseCommander] = [
    yc.Soldier(keywords=["change"], command="chown user:group file", description=""),
    yc.Soldier.from_dict(
        {
            "keywords": ["ls", "seconds"],
            "command": "ls --time-style=full-iso -all",
            "description": "show time in nano second",
        }
    ),
]
chief_commander = yc.Commander(commanders)
