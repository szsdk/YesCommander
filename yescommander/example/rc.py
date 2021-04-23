from typing import List
import yescommander as yc

commanders: List[yc.BaseCommander] = [
    yc.Soldier(keywords=["change"], command="chown user:group file", description=""),
    yc.Soldier(
        ["ls", "seconds"], "ls --time-style=full-iso -all", "show time in nano second"
    ),
]
chief_commander = yc.Commander(commanders)
