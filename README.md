# Sanity Price Monitor
Determines 

# Installing
## Clone the repo
This repo makes use of the [smart-contracts](https://github.com/KyberNetwork/smart-contracts) as a submodule for it's 
configuration, so to clone this repo run:
    
    $ git clone https://github.com/KyberNetwork/sanity-price-monitor.git --recursive
    
## Installing library dependencies
Enter the folder and use pipenv to install library dependencies:

    $ cd sanity-price-monitor
    $ pipenv install
    
## Running coverage

    $ cd sanity-price-monitor/tests
    $ py.test --cov-report html --cov=pricemonitor --verbose && open htmlcov/index.html
