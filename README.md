# mtg-analytics
### v0.0
Python/React full stack application that models data from TCGPlayer API (stored in mongodb) and tries to find price patterns.

## Why Price?
With different formats that get cards added and removed constantly, the metagame constantly evolving, there seem to be certain cards, both old and new, that get price changes. Using the median market price from each card, its possible to see some price fluctuation. Seeing this price data modeled in some front end graphical interface could help people know when its best to buy and see what cards where mostly being purchased with what other cards at a given period of time. 

## Tech/Framework's Used
    * Python (3.7.4)
    * mongodb
    * TCGPlayer API (1.27.0)
        * ADE Tool _ex. Postman_

## How To Run?
_[Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installing/) needs to be properly installed in order to run application_
_[TCGPlayer API Key](http://developer.tcgplayer.com/) required in order to query API_

1. run `pip install -r requirements.txt` in the current directory to install all the dependencies required.
2. running `python3 mtg_analytics_serverside.py` should automatically begin to run the project.
3. Thats it! (for now ;))

## Contributors
    * Martin Liriano