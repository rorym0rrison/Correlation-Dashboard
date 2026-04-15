
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import pandas as pd
import numpy as np
import yfinance as yf

class CorrelationDashboard:
    def __init__(self, root):

        self.root = root

        self.root.title('Correlation Dashboard')
        self.root.geometry('1400x900')

        # data holders
        self.equity_data_1: pd.DataFrame | None = None
        self.equity_data_2: pd.DataFrame | None = None
        self.merged_equity_data: pd.DataFrame | None = None

        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # data query frame
        data_frame = ttk.LabelFrame(main_frame, text='Data Query', padding='5')
        data_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))
        data_frame.columnconfigure(9, weight=10)

        self.analyze_btn = ttk.Button(data_frame, text='Analyze Correlation', command=self.analyze_correlation)
        self.analyze_btn.grid(row=0, column=7, padx=(0,10), sticky=tk.W)

        ttk.Label(data_frame, text='Duration:').grid(row=0, column=1, padx=(0,5), sticky=tk.W)
        self.duration_var = tk.StringVar(value='1y')
        duration_options = ['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max']

        self.duration_combo = ttk.Combobox(
            data_frame,
            textvariable=self.duration_var,
            values=duration_options,
            width=8,
            state='readonly'
        )
        self.duration_combo.grid(row=0, column=0, padx=(0,15), sticky=tk.W)


        # inputs for the two assets to test 
        ttk.Label(data_frame, text='Symbol 1'). grid(row=0, column=1, padx=(0,10))
        self.symbol_1_var = tk.StringVar(value='AAPL')
        ttk.Entry(data_frame, textvariable=self.symbol_1_var, width=10).grid(row=0, column=2, padx=(0,10))

        ttk.Label(data_frame, text='Symbol 2'). grid(row=0, column=3, padx=(0,10))
        self.symbol_2_var = tk.StringVar(value='NVDA')
        ttk.Entry(data_frame, textvariable=self.symbol_2_var, width=10).grid(row=0, column=4, padx=(0,10))


        self.query_btn = ttk.Button(data_frame, text='Query Data', command = self.query_data)
        self.query_btn.grid(row=0, column=6, padx=(0,10))


        # correlation frame
        cor_frame = ttk.LabelFrame(main_frame, text='Correlation', padding='10')
        cor_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0,10))

        ttk.Label(cor_frame, text='Correlation  (Log Returns):').grid(row=0, column=0, padx=(0,5))
        self.correlation_label = ttk.Label(cor_frame, text='N/A', font=('Arial', 10))
        self.correlation_label.grid(row=0, column=1, padx=(0,20), sticky=tk.W)

        ttk.Label(cor_frame, text='Regression:').grid(row=0, column=2, padx=(0,5), sticky=tk.W)
        self.regression_label = ttk.Label(cor_frame, text='N/A', font=('Arial', 10))
        self.regression_label.grid(row=0, column=3, sticky=tk.W)


        # status frame
        status_frame = ttk.LabelFrame(main_frame, text='Status', padding='5')
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0,10))
        status_frame.columnconfigure(0, weight=1)


        self.status_text = scrolledtext.ScrolledText(status_frame, height=12, width=160)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)


        # plot frame
        plot_frame = ttk.LabelFrame(main_frame, text='Plots', padding='10')
        plot_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(14,5))
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # function for taking messages and then adding them to the status frame
    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.status_text.insert(tk.END, f'[{timestamp}] {message}\n')
        self.status_text.see(tk.END) 
        self.root.update_idletasks()


    def query_data(self):

        symbol_1 = self.symbol_1_var.get().strip().upper()
        symbol_2 = self.symbol_2_var.get().strip().upper()

        if not symbol_1 or not symbol_2:
            messagebox.showerror('Error, Please Enter Both Symbols')
            return
        if symbol_1 == symbol_2:
            self.log_message('Please Enter Two Different Symbols')
            return

        period = self.duration_var.get()
        self.log_message(f'Downloading daily data from Yahoo Finance for {symbol_1} & {symbol_2}')

        self.analyze_btn.config(state='disabled')
        self.correlation_label.config(text='N/A')
        self.regression_label.config(text='N/A')
        self.merged_equity_data = None

        try:
            df = yf.download(
                tickers=[symbol_1, symbol_2],
                period=period,
                interval='1d',
                auto_adjust=True,
                group_by='column',
                progress=False,
                threads=True
            )

            # validate that both are recieved
            if df is None or df.empty:
                self.log_message('No data returned')
                return

            # multiple tickers
            if not isinstance(df.columns, pd.MultiIndex):
                # if yfinance flatttened, fetch individually
                d1 = yf.download(
                                symbol_1, 
                                period=period,
                                interval='1d',
                                auto_adjust='True',
                                progress=False
                            )
                
                d2 = yf.download(
                                symbol_2, 
                                period=period,
                                interval='1d',
                                auto_adjust='True',
                                progress=False
                            )
                
                if d1.empty or d2.empty:
                    self.log_message('No data returned for both symbols.')
                    return
                s1 = d1['Close'].rename(f'close_{symbol_1}')
                s2 = d1['Close'].rename(f'close_{symbol_2}')
            else:
                close = df['Close'].copy()
                if symbol_1 not in close.columns or symbol_2 not in close.columns:
                    self.log_message('Close series missing for one or both symbols (ticker(s) may be invalid).')
                    return
                s1 = close[symbol_1].rename(f'close_{symbol_1}')
                s2 = close[symbol_2].rename(f'close_{symbol_2}')
            
            df1 = s1.to_frame()
            df2 = s2.to_frame()

            merged = df1.join(df2, how='inner').dropna()
            if merged.empty:
                self.log_message('No overlapping dates after alignment (merge dataset is empty)')
                return
            
            self.equity_data_1 = df1
            self.equity_data_2 = df2
            self.merged_equity_data = merged

            self.log_message(f'Recieved {len(df1)} closes for {symbol_1}')
            self.log_message(f'Recieved {len(df2)} closes for {symbol_2}')
            self.log_message(f'Align rows: {len(merged)}')
            self.log_message(f'Date range: {merged.index.min()} to {merged.index.max()}')

            self.analyze_btn.config(state='normal')

        except Exception as e:
            self.log_message(f'yfinance error: {e}')




    def analyze_correlation(self):

        if self.merged_equity_data is None or self.merged_equity_data.empty:
            messagebox.showerror('Error, No Price Data Available for Analysis')
            return
        
        self.log_message('Analyzing Price Data')

        symbol_1 = self.symbol_1_var.get().strip().upper()
        symbol_2 = self.symbol_2_var.get().strip().upper()

        c1 = f'close_{symbol_1}'
        c2 = f'close_{symbol_2}'

        df = self.merged_equity_data[[c1, c2]].dropna()
        if df.empty or len(df) < 3:
            messagebox.showerror('Error, not enough aligned data for analysis')

        # converts to log space, then finds the correlation using .corr().
        # final correlation value is just taken as row 0 column 1
        log_returns = np.log(df).diff().dropna()
        corr = log_returns.corr().iloc[0, 1]
        self.log_message(f'Correlation (log returns): {corr:.4}')

        # regression
        x = log_returns[c1].to_numpy()
        y = log_returns[c2].to_numpy()

        if len(x) < 2:
            messagebox.showerror('Error, Not enough data points for regression')
            return
        
        slope, intercept = np.polyfit(x, y, deg=1)

        # R^2
        y_hat = intercept + slope * x
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot if ss_tot != 0 else np.nan)

        self.log_message(f'Regression (log returns): y = {intercept:.6f} + {slope: .4f}x, R^2 = {r2:.4f}')

        # update the ui
        self.correlation_label.config(text=f'{corr:.4f}')
        self.regression_label.config(text=f'y = {intercept:.6f} + {slope:.4f} | R²={r2:.4f}')

        # plots
        self.ax1.clear()
        self.ax2.clear()

        self.ax1.plot(df.index, df[c1], label=c1, linewidth=1.5)
        self.ax1.plot(df.index, df[c2], label=c2, linewidth=1.5)

        self.ax1.set_title(f'Timeseries of {symbol_1} & {symbol_2}')
        self.ax1.set_xlabel(f'Date')
        self.ax1.set_ylabel(f'Price')
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)

        
        self.ax2.scatter(x, y, alpha=0.6, s=20)

        # regression line
        x_range = np.linspace(x.min(), x.max(), 200)
        self.ax2.plot(
            x_range,
            intercept + slope * x_range,
            linewidth=2,
            label=f'y = {slope:.3f}x + {intercept:.3f}, R^2={r2:.3f}'
        )

        self.ax2.set_title(f'Linear Regression: {c1} vs {c2}')
        self.ax2.set_xlabel(c1)
        self.ax2.set_ylabel(c2)
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw_idle()

def main():
    root = tk.Tk()
    _ = CorrelationDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()


