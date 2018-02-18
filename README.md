# Sanity Price Monitor
Determines maximum conversion rates for the main contract.

# Installing
## Clone the repo
This repo makes use of the [smart-contracts](https://github.com/KyberNetwork/smart-contracts) as a submodule for it's 
configuration, so to clone this repo run:
    
    $ git clone https://github.com/KyberNetwork/sanity-price-monitor.git --recursive
    
## Installing library dependencies
Enter the folder and use pipenv to install library dependencies:

    $ cd sanity-price-monitor
    $ pipenv install
    
## Running the monitor

    $ cd sanity-price-monitor
    $ pipenv shell
    $ python -m pricemonitor.monitor
    
## Running coverage

    $ cd sanity-price-monitor/tests
    $ pipenv shell
    $ py.test --cov-report html --cov=pricemonitor --verbose && open htmlcov/index.html
