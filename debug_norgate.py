import norgatedata
import traceback
from src.data.loader import NorgateLoader

def debug_norgate():
    print("Initializing NorgateLoader...")
    try:
        loader = NorgateLoader()
        print("Loader initialized. Testing BTC load...")
        # The user said BTC ticker is 'BTC-USD'
        # loader.load_price_history('BTC') maps 'BTC' -> 'BTC-USD' internally now
        df = loader.load_price_history('BTC', n_days=30)
        print("Success!")
        print(df)
    except Exception as e:
        print("\n=== CAUGHT EXCEPTION ===")
        print(f"Type: {type(e)}")
        print(f"Str: {str(e)}")
        print(f"Repr: {repr(e)}")
        print("\n=== TRACEBACK ===")
        traceback.print_exc()

if __name__ == "__main__":
    debug_norgate()
