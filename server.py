from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
from backtest import load_data, Backtester

app = FastAPI()

@app.post('/backtest')
async def run_backtest(file: UploadFile = File(...), from_tz: str = 'US/Central'):
    try:
        contents = await file.read()
        df = pd.read_csv(pd.compat.StringIO(contents.decode()))
        df = load_data(df, from_tz=from_tz)
        bt = Backtester(df)
        bt.run()
        summary = bt.summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
