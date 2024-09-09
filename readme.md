# Yahoo Finance Scraper

This Python script utilizes Selenium to scrape historical stock data from Yahoo Finance. It allows users to specify a stock symbol and fetch data into a pandas DataFrame.

## Prerequisites

Make sure you have Python installed on your system.

## Installation

1. Clone this repository:

    ```
    git clone https://github.com/yourusername/stock-data-scraper.git
    ```

2. Navigate to the project directory:

    ```
    cd yahoo-finance-scraper
    ```

3. Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

## Configuration

The `config.json` file contains the following configurations:

- `stock_symbol`: Specify the stock symbol you want to fetch data for.
- `fetching_data`: Set to `true` if you want to fetch fresh data, otherwise set to `false`.

## Run the script

```
    python scraper.py
```

## Sample Output

Upon running the script, the historical stock data will be displayed in the console and saved in a text file in the `raw_data` folder.