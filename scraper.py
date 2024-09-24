from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time,json,os,subprocess
import numpy as np
from fake_useragent import UserAgent


def update_data(stock_symbol : str, raw_data_file : str, time_frame : str):

    try:
        options = webdriver.ChromeOptions()
        user_agent = UserAgent()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--log-level=3")
        options.add_argument('--no-proxy-server')
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        #options.add_argument(f'user-agent={user_agent.random}')
        driver = webdriver.Chrome(options=options)

        driver.get("https://finance.yahoo.com/quote/"+stock_symbol+"/history")
        #time.sleep(50000)
        # click on the button refuse cookies            
        button = driver.find_element(by=By.XPATH, value="/html/body/div/div/div/div/form/div[2]/div[2]/button[2]")
        time.sleep(2)
        button.click()

        # click on the button to select time frame
        # tertiary-btn fin-size-small menuBtn rounded yf-1al6vaf
                                                        #/html/body/div[2]/main/section/section/section/article/div[1]/div[1]/div[1]/button/span
        button = driver.find_element(by=By.XPATH, value="/html/body/div[2]/main/section/section/section/article/div[1]/div[1]/div[1]/button")
        time.sleep(2)
        button.click()

        tab = ['1D', '5D', '3M', '6M', '1Y', '2Y', '5Y', 'MAX']
        
        # click on time frame
        button_number = tab.index(time_frame.upper())+1
        button = driver.find_element(by=By.XPATH, value='/html/body/div[2]/main/section/section/section/article/div[1]/div[1]/div[1]/div/div/div[2]/section/div[1]/button['+str(button_number)+']')
        button.click()

        # fetch the data
        file=open(raw_data_file,"w")
        file.write("")
        data = driver.find_elements(by=By.CLASS_NAME, value='yf-ewueuo')
        for item in data:
            file.write(item.text)

        # close the file and the driver
        file.close()
        time.sleep(2)
        driver.quit()
        subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
    except:
        print("Error while updating data")
        pass

def transform(raw_data_file : str) -> list[str]:

    file = open(raw_data_file, "r")
    raw_data = file.readlines()
    raw_data.remove(raw_data[0])
    raw_data.remove(raw_data[0])
    raw_data.remove(raw_data[0])
    cleaned_lines = []
    for line in raw_data:
        if "Date" in line:
            break
        cleaned_lines.append(line)
    file.close()
    return cleaned_lines



def create_df(raw_data_file : str) -> pd.DataFrame:
    raw_data = transform(raw_data_file)
    data = [[] for _ in range(len(raw_data))]
    for i in range(len(raw_data)):
        raw_data[i] = raw_data[i].replace("\n", "")
        data[i] = data_to_table(raw_data[i])

    data = [row for row in data if "Dividend" not in row]
    data = [row for row in data if "Stock" not in row]
    data = [row for row in data if "-" not in row]
    head=["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    df = pd.DataFrame(data, columns=head)
    # Convert columns to float
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Adj Close"] = df["Adj Close"].astype(float)
    df["Volume"] = df["Volume"].astype(float)
    df['Date'] = pd.to_datetime(df['Date'])

    return df


def data_to_table(string : str) -> list[str]:
    string = string.replace(",", "")
    parts = string.split(" ")
    date =  ' '.join(parts[:3])
    parts = parts[2:]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dates = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    for i in range(len(months)):
        if months[i] in date:
            date = date.replace(months[i], dates[i])
    date = date.replace(" ", "/")
    parts[0] = date
    parts[-1] = parts[-1].replace(",", "")
    return parts

def indicators(df : pd.DataFrame) -> pd.DataFrame:
    # Simple Moving Average (SMA)
    df['SMA_10'] = df['Close'].rolling(window=10).mean()

    # Exponential Moving Average (EMA)
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()

    # Relative Strength Index (RSI)
    delta = df['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # Moving Average Convergence Divergence (MACD)
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    sma_20 = df['Close'].rolling(window=20).mean()
    std_20 = df['Close'].rolling(window=20).std()
    df['Bollinger_High'] = sma_20 + (std_20 * 2)
    df['Bollinger_Low'] = sma_20 - (std_20 * 2)

    # Average True Range (ATR)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = high_low.combine(high_close, max).combine(low_close, max)
    df['ATR_14'] = tr.rolling(window=14).mean()

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['%K'] = (df['Close'] - low_14) * 100 / (high_14 - low_14)
    df['%D'] = df['%K'].rolling(window=3).mean()

    # On-Balance Volume (OBV)
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

    # Rate of Change (ROC)
    n = 10
    df['ROC_10'] = ((df['Close'] - df['Close'].shift(n)) / df['Close'].shift(n)) * 100

    # Commodity Channel Index (CCI)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma_tp = tp.rolling(window=20).mean()
    md = tp.rolling(window=20).apply(lambda x: np.fabs(x - x.mean()).mean())
    df['CCI_20'] = (tp - sma_tp) / (0.015 * md)

    return df



def main():

    print("\n-----------------------------------------------------------------------------------------------\n")

    # open the config file
    with open('config.json') as config_file:
        config = json.load(config_file)
        stock_symbol = config["stock_symbol"]
        fetching_data = config["fetching_data"]
        time_frame = config["time_frame"]

    # Create the folder of raw data if it doesn't exist
    folder_name = "raw_data"
    folder_path = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


    raw_data_file=folder_name+"/"+stock_symbol+".txt"

    if fetching_data == True:
        print(f"Fetching data for {stock_symbol}...\n")
        update_data(stock_symbol, raw_data_file, time_frame)

    if os.path.isfile(raw_data_file):
        print("Dataframe of " + stock_symbol+"\n\n")
        df = create_df(raw_data_file)
        #df = indicators(df)
        print(df)
        df.to_csv('stock_data.csv', index=False)
        return df
    else:
        print("No data found for " + stock_symbol)
        print("Please check your config.json file,\nChange fething_data to True if you want to fetch data.\n")

    print("\n-----------------------------------------------------------------------------------------------\n")


if __name__ == "__main__":
    main()