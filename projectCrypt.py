import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

from datetime import datetime

from numpy.ma.extras import corrcoef

# Inicjalizacja giełdy
exchange = ccxt.binance()

# Pobieranie danych historycznych dla BTC/USDT (1h interwał)
symbol = 'BTC/USDT'
timeframe = '1h'
since = exchange.parse8601('2024-01-01T00:00:00Z')  # Od kiedy pobrać dane
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Konwersja do DataFrame
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Zapis do pliku CSV
df.to_csv('btc_usdt_1h.csv', index=False)
print(df.tail())
import requests
import pandas as pd

import requests
import pandas as pd


def get_coingecko_data(coin_id='bitcoin', vs_currency='usd', days=30, interval='hourly'):
    # Budujemy URL do API CoinGecko
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}"

    try:
        # Pobieramy dane
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Wyciągamy dane
        prices = data['prices']
        market_caps = data['market_caps']
        total_volumes = data['total_volumes']

        # Tworzymy DataFrame dla cen
        df_prices = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')

        # Tworzymy DataFrame dla kapitalizacji i wolumenu
        df_market_caps = pd.DataFrame(market_caps, columns=['timestamp', 'market_cap'])
        df_market_caps['timestamp'] = pd.to_datetime(df_market_caps['timestamp'], unit='ms')
        df_volumes = pd.DataFrame(total_volumes, columns=['timestamp', 'volume'])
        df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp'], unit='ms')

        # Agregacja danych do OHLC
        if interval == 'hourly':
            freq = 'H'  # Godzinowy interwał
        elif interval == 'daily':
            freq = 'D'  # Dzienny interwał
        else:
            raise ValueError("Interval musi być 'hourly' lub 'daily'")

        # Grupujemy ceny po interwale czasowym i obliczamy OHLC
        df_ohlc = df_prices.groupby(pd.Grouper(key='timestamp', freq=freq)).agg({
            'price': [
                ('open', 'first'),  # Pierwsza cena w interwale
                ('high', 'max'),  # Najwyższa cena
                ('low', 'min'),  # Najniższa cena
                ('close', 'last')  # Ostatnia cena
            ]
        })

        # Spłaszczamy nazwy kolumn
        df_ohlc.columns = df_ohlc.columns.droplevel(0)
        df_ohlc = df_ohlc.reset_index()

        # Agregacja kapitalizacji (bierzemy ostatnią wartość w interwale)
        df_market_caps = df_market_caps.groupby(pd.Grouper(key='timestamp', freq=freq)).agg({
            'market_cap': 'last'
        }).reset_index()

        # Agregacja wolumenu (suma w interwale)
        df_volumes = df_volumes.groupby(pd.Grouper(key='timestamp', freq=freq)).agg({
            'volume': 'sum'
        }).reset_index()

        # Łączymy wszystkie dane
        df = df_ohlc.merge(df_market_caps, on='timestamp').merge(df_volumes, on='timestamp')

        return df

    except requests.RequestException as e:
        print(f"Error downloading data: {e}")
        return None


# Pobieramy dane
df = get_coingecko_data(coin_id='bitcoin', vs_currency='usd', days=30, interval='hourly')

if df is not None:
    # Zapisujemy do pliku CSV
    df.to_csv('bitcoin_ohlc.csv', index=False)

    # Wyświetlamy pierwsze 5 wierszy
    print(df.head())
else:
    print("Failed to download data.")

print(df)

print(df.columns)
plt.figure(figsize=(12, 6))  # Ustawiamy większy rozmiar wykresu
plt.plot(df['timestamp'], df['close'], label='Close price (USD)', color='blue')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Format daty: RRRR-MM-DD
# 2. Ustawiamy lokator etykiet (np. co 5 dni)
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))  # Pokazuj etykiety co 5 dni
# 3. Obracamy etykiety o 45 stopni dla lepszej czytelności

plt.show()

fig = go.Figure(data= [go.Candlestick(x=df['timestamp'],
                                      open=df['open'],
                                      high=df['high'],
                                      low=df['low'],
                                      close=df['close']),])
fig.update_layout(    title='Bitcoin Candlestick Chart (BTC/USD)',
    xaxis_title='Data',
    yaxis_title='Cena (USD)',
    xaxis_rangeslider_visible=False
)
fig.show()
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Wczytanie danych
df = pd.read_csv('bitcoin_ohlc.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Wykres
fig, ax1 = plt.subplots(figsize=(12, 6))

# Cena zamknięcia
ax1.plot(df['timestamp'], df['close'], label='Close price (USD)', color='blue')
ax1.set_xlabel('Data')
ax1.set_ylabel('Cena (USD)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Wolumen
ax2 = ax1.twinx()
ax2.bar(df['timestamp'], df['volume'], label='Wolumen (USD)', color='gray', alpha=0.3)
ax2.set_ylabel('Wolume', color='gray')
ax2.tick_params(axis='y', labelcolor='gray')

# Formatowanie osi X
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
plt.xticks(rotation=45)

# Tytuł i układ
plt.title('Price and volume  Bitcoina (BTC/USD)')
fig.tight_layout()
fig.legend(loc='upper center', ncol=2)
plt.show()

df['returns'] = df['close'].pct_change() * 100

plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['returns'], label='Zwroty procentowe (%)', color='purple')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
plt.xticks(rotation=45)
plt.title('Bitcoin (BTC/USD) Percentage Returns')
plt.xlabel('Data')
plt.ylabel('Return (%)')
plt.legend()
plt.tight_layout()
plt.show()



df_daily = df.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
    'open': 'first',   # Pierwsza cena dnia
    'high': 'max',     # Najwyższa cena dnia
    'low': 'min',      # Najniższa cena dnia
    'close': 'last',   # Ostatnia cena dnia
    'volume': 'sum'    # Suma wolumenu
}).reset_index()
df_daily['spread']=df_daily['high']-df_daily['low']
plt.figure(figsize=(12, 6))
plt.plot(df_daily['timestamp'], df_daily['spread'],label='Daily spread (USD)', color='blue')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
plt.xticks(rotation=45)
plt.title('Bitcoin price fluctuations during the day (Spread high-low))')
plt.xlabel('Data')
plt.ylabel('Spread (USD)')
plt.legend()
plt.tight_layout()
plt.show()
ticker = "GC=F"

# Oblicz daty: dzisiaj i 30 dni wstecz
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Pobierz dane historyczne
gold_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)

gold_data = gold_data.reset_index()  # Konwersja indeksu Date na kolumnę
gold_data.columns = gold_data.columns.get_level_values(0)  # spłaszczenie kolumn

gold_data['timestamp'] = pd.to_datetime(gold_data['Date']).dt.tz_localize(None)  # Usunięcie strefy czasowej
print(gold_data)


print(df_daily)

df_combined = df_daily.rename(columns={'close': 'bitcoin_price'}).merge(
    gold_data[['timestamp', 'Close']].rename(columns={'Close': 'gold_price'}),
    on='timestamp',
    how='inner'
)
print(df_combined.columns)
plt.figure(figsize=(12, 6))

# Oś dla Bitcoina (lewa)
ax1 = plt.gca()
ax1.plot(df_combined['timestamp'], df_combined['bitcoin_price'], label='Bitcoin (USD)', color='blue')
ax1.set_xlabel('Data')
ax1.set_ylabel('Bitcoin price (USD)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Oś dla złota (prawa)
ax2 = ax1.twinx()
ax2.plot(df_combined['timestamp'], df_combined['gold_price'], label='Gold  (USD)', color='gold')
ax2.set_ylabel('Gold price (USD)', color='gold')
ax2.tick_params(axis='y', labelcolor='gold')

# Formatowanie osi X
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
plt.xticks(rotation=45)

# Tytuł i legenda
plt.title(' Bitcoina vs Gold price (last 30 days)')
fig = plt.gcf()
fig.legend(loc='upper center', ncol=2)


plt.tight_layout()
plt.show()
