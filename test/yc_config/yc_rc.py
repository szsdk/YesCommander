from typing import List

import yescommander as yc

commanders: List[yc.BaseCommander] = [
    yc.Soldier.from_dict(
        {
            "keywords": ["ls", "seconds"],
            "command": f"cmd {i}",
        }
    )
    for i in range(10)
]
chief_commander = yc.Commander(commanders)
