# PrismataBot
A Twitch bot that gives you info on Prismata units.

The bot will automatically join any channel streaming Prismata and provide the viewers with useful commands.

It is currently running on an AWS EC2 instance using the scripts in the `scripts` folder.

## Commands

`!unit X`: Displays information about unit X. The bot is very lenient with typos and will try to match individual words of unit names. For instance, `!unit pahge` will match to "phage" which matches to "Blood Phage".

`!prismata X`: Displays a pre-coded message about topic X. [Topics and responses can be seen here.](data/prismata_responses.json)

## Starting the bot

* Use Python 3
* `pip install -r requirements.txt`
* Run [`src/bot_manager.py`](src/bot_manager.py)
* To update unit tooltips that are stored in [`data/unit_tooltips.json`](data/unit_tooltips.json), run [`src/get_units.py`](src/get_units.py)
