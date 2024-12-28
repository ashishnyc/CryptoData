import argparse
from dataManagers.ByBitMarketDataManager import ByBitDataIngestion, ByBitDataService
import utils

bbDi = ByBitDataIngestion()
bbDs = ByBitDataService()

instruments = bbDs.get_linear_usdt_instruments(quote_coin="USDT", data_source="db")
for instrument in instruments:
    print(f"Processing pivot levels for {instrument.symbol}")
    bbDi.process_pivot_levels(symbol=instrument.symbol)
print("done")
