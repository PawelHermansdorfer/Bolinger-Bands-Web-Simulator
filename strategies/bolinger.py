import yfinance as yf
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime as dt


class Bolinger:
    def __init__(self,
               stock_ticker: str,
               date_period: tuple | None = None, 
               period: str = '1y',
               interval = '1d',
               window: int = 20,
               bands_spread: float = 2,
               display_period = None) -> None:
        if date_period:
            df = yf.download(tickers=stock_ticker, interval=interval,
                            start=date_period[0], end=date_period[1], 
                            progress=False).copy()
        else:
            df = yf.download(tickers=stock_ticker, interval=interval,
                            period=period, progress=False).copy()
        
        df['Sma'] = df['Close'].rolling(window=window).mean()
        df['Std'] = df['Close'].rolling(window=window).std()
        df = df.dropna()
        
        df['Upper_band'] = df['Sma'] + (df['Std'] * bands_spread)
        df['Lower_band'] = df['Sma'] - (df['Std'] * bands_spread)
        
        df['Buy'] = df['Close'] < df['Lower_band']
        df['Sell'] = df['Close'] > df['Upper_band']

        df = df
        open_pos = True
        transactions = []
        
        for index, row in df[(df['Buy'] == True) | (df['Sell'] == True)].iterrows():
            if open_pos:
                if row['Buy'] == True:
                    open_pos = False
                    transactions.append({'index': index, 'data': row})
            else:
                if row['Sell'] == True:
                    open_pos = True
                    transactions.append({'index': index, 'data': row}) 
        
        
        try:
            tick_long_name = yf.Ticker(stock_ticker).info['longName']
            self.full_name = (tick_long_name
                              if tick_long_name is not None
                              else stock_ticker)
        except KeyError as error:
            if 'longName' in error.args:
                self.full_name = stock_ticker 
            
        self.stock_ticker = stock_ticker
        self.date_period = date_period
        self.df = df
        self.transactions = transactions
        

    def return_rate(self):
        if len(self.transactions) > 1:
            return_rates = []    
            for i in range(0, len(self.transactions)-1, 2):
                """
                Len(transactions) = even -> Iterates every second row, subtracting next. Last element is SELL order so in range is len-1 in order not to pop IndexError
                Len(transactions) = odd -> Iterates every second row, subtracting next. Last element is BUY so thanks to len-1 in step being 2 it skips last, uneven row.
                In conclusion it calculates profit of every ended position
                """ 
                transaction_profit = (self.transactions[i+1]['data']['Close'] 
                                    - self.transactions[i]['data']['Close'])
                return_rates.append(transaction_profit
                                    / self.transactions[i]['data']['Close']
                                    * 100) 
            
            return np.mean(return_rates)
        return None
    
    
    def plotly_json(self):
        title = ('<b>'
                 + (f'{self.stock_ticker} - {self.full_name}' 
                 if self.stock_ticker != self.full_name 
                 else f'{self.stock_ticker}')
                 + ' </b>')
        
        title += ('<i><br>'
                  + f'{self.df.index[0].strftime("%d.%m.%Y")}'
                  + ' - '
                  + f'{self.df.index[-1].strftime("%d.%m.%Y")}') + '</i>'
        
        
        title += '<br>' + (f'Estimated return rate: {round(self.return_rate(), 2)}%'
                           if self.return_rate()
                           else f'Not enough transactions to estimate rate of return')

        fig = go.Figure(data=[go.Candlestick(x=self.df.index,
                                             open=self.df.Open,
                                             high=self.df.High,
                                             low=self.df.Low,
                                             close=self.df.Close,
                                             name='Price')])
        fig.add_trace(go.Scatter(x=self.df.index,
                                 y=self.df.Sma,
                                 line=dict(color='#e0e0e0'),
                                 name='SMA'))
        # BANDS
        fig.add_trace(go.Scatter(x=self.df.index,
                                 y=self.df.Upper_band,
                                 line=dict(color='orange',
                                           width=1.5),
                                 name='Upper band'))
        fig.add_trace(go.Scatter(x=self.df.index,
                                 y=self.df.Lower_band,
                                 line=dict(color='orange',
                                           width=1.5),
                                 name='Lower band'))
        
        fig.add_trace(go.Scatter(mode='markers',
                                 x=self.df[self.df.Buy == True].index,
                                 y=self.df[self.df.Buy == True].Close,
                                 marker_color='green',
                                 marker_symbol='triangle-up',
                                 marker_size=12,
                                 name='Buy'))
        
        fig.add_trace(go.Scatter(mode='markers',
                                 x=self.df[self.df.Sell == True].index,
                                 y=self.df[self.df.Sell == True].Close,
                                 marker_color='red',
                                 marker_symbol='triangle-down',
                                 marker_size=12,
                                 name='Sell'))
        
        fig.update_layout(xaxis_rangeslider_visible=False,
                          template='plotly_dark',
                          yaxis_title=f'{self.stock_ticker} price (USD)',
                          xaxis_title='Date',
                          title=title,
                          title_font_size=18,
                          title_x=0.5,
                          autosize=True)
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)