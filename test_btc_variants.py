import norgatedata
from src.data.loader import NorgateLoader

def try_symbol(sym):
    print(f"Testing symbol: '{sym}'")
    try:
        nd = norgatedata
        ts = nd.price_timeseries(
             sym,
             stock_price_adjustment_setting=nd.StockPriceAdjustmentType.TOTALRETURN,
             padding_setting=nd.PaddingType.NONE
        )
        if ts is not None:
             print(f"SUCCESS: Found data for '{sym}'")
        else:
             print(f"FAILURE: No data for '{sym}'")
    except Exception as e:
        print(f"ERROR for '{sym}': {e}")

if __name__ == "__main__":
    variants = ["BTC-USD", "BTCUSD", "$XBTUSD", "BTC.CC", "BTC-USD.CC"]
    for v in variants:
        try_symbol(v)
