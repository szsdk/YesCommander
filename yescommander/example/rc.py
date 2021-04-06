import yescommander as yc
commands = [
        (['ls', 'seconds'], 'ls --time-style=full-iso -all', 'show time in nano second'),
        (['find', 'name'], 'find ./ -name "*.foo"'),
        ([], 'grep --exclude-dir={build,} match * -r'),
        (['python'], "python3 -m http.server"),
        (['compress'], "zip a.zip A -r"),
        (['change'], "chown user:group file"),
        yc.Command([], 'vim -u NONE', 'open vim without vimrc'),
        ]
