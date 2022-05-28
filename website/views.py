from flask import Blueprint, render_template, request, abort
from strategies.bolinger import Bolinger
from datetime import datetime, timedelta
import dateutil.relativedelta

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html')

@views.route('/bollinger-bands', methods=["POST", "GET"])
def bollinger_bands():
    if request.method == 'POST':
        stocks_names = request.form['stocks_names']

        if stocks_names != '':
            stocks_names = stocks_names.split(',')
            stocks_names = [s.strip(' ').upper() for s in stocks_names]

        generated_data = []
        for stock in stocks_names:
            end_date = (datetime.strptime(request.form['end_date'], '%Y-%m-%d')
                        + timedelta(days=1))
            time_period = request.form['time_period']
            match time_period:
                case '6mo':
                    start_date = end_date - dateutil.relativedelta.relativedelta(months=6, days=20)
                case '1y':
                    start_date = end_date - dateutil.relativedelta.relativedelta(years=1, days=20)
                case '2y':
                    start_date = end_date - dateutil.relativedelta.relativedelta(years=2, days=20)
                case '5y':
                    start_date = end_date - dateutil.relativedelta.relativedelta(years=5, days=20)
                case '10y':
                    start_date = end_date - dateutil.relativedelta.relativedelta(years=10, days=20)
                case _:     
                    bolinger_analyze = Bolinger(stock_ticker=stock,
                                                period=time_period)
            
            if time_period not in ['ytd', 'max']:
                bolinger_analyze = Bolinger(stock_ticker=stock,
                                            date_period=(start_date, end_date))
                
            if len(bolinger_analyze.df) == 0: 
                return render_template('bollinger_bands.html',
                                        generated_data='Incorrect tickers',
                                        inputs = stocks_names)
                
            plot_img = bolinger_analyze.plotly_json()
            return_rate = (round(bolinger_analyze.return_rate(), 2)
                           if bolinger_analyze.return_rate()
                           else None)
            
            generated_data.append({'name': bolinger_analyze.full_name,
                                   'plot_img': plot_img,
                                   'return_rate': return_rate})
            
        return render_template('bollinger_bands.html',
                               generated_data=generated_data)
        
    else:
        return render_template('bollinger_bands.html',
                               generated_data=None)