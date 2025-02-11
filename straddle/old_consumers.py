import os
import json
import asyncio
import datetime
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv
from .models import StraddlePrice




load_dotenv()

ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FYERS_CLIENT_ID")

if not ACCESS_TOKEN or not CLIENT_ID:
    raise ValueError("Missing Fyers API credentials. Check your .env file.")

fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN, is_async=False)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

price_history = {"timestamps": [], "nifty_straddle": [], "sensex_straddle": [],"bankex_straddle":[],"finnifty_straddle":[],"midcapnifty_straddle":[],"banknifty_straddle":[]}
logger = logging.getLogger(__name__)

class StraddleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        logging.info("WebSocket Connection Established.")
        self.is_active = True
        asyncio.create_task(self.fetch_and_send_data())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        self.is_active = False
        logging.warning(f"WebSocket Disconnected. Close Code: {close_code}")

    async def fetch_and_send_data(self):
        while self.is_active:
            try:
                nifty_data = await asyncio.to_thread(self.get_atm_straddle, "NIFTY50") 
                sensex_data = await asyncio.to_thread(self.get_atm_straddle, "SENSEX")
                bankex_data = await asyncio.to_thread(self.get_atm_straddle, "BANKEX")
                finnifty_data = await asyncio.to_thread(self.get_atm_straddle, "FINNIFTY")
                midcapnifty_data = await asyncio.to_thread(self.get_atm_straddle, "MIDCPNIFTY")
                banknifty_data = await asyncio.to_thread(self.get_atm_straddle, "NIFTYBANK")
                
                

                # BANKNIFTY




                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                if nifty_data:
                    atm_strike, call_price, put_price,ltp = nifty_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "NIFTY50", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["timestamps"].append(timestamp)
                    price_history["nifty_straddle"].append(straddle_price)
                    

                if sensex_data:
                    atm_strike, call_price, put_price ,ltp= sensex_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "SENSEX", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["sensex_straddle"].append(straddle_price)


                
                if bankex_data:
                    atm_strike, call_price, put_price,ltp = bankex_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "BANKEX", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["bankex_straddle"].append(straddle_price)


                
                if finnifty_data:
                    atm_strike, call_price, put_price ,ltp= finnifty_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "FINNIFTY", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["finnifty_straddle"].append(straddle_price)

                

                if midcapnifty_data:
                    atm_strike, call_price, put_price ,ltp= midcapnifty_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "MIDCPNIFTY", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["midcapnifty_straddle"].append(straddle_price)


                
                if banknifty_data:
                    atm_strike, call_price, put_price,ltp = banknifty_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "NIFTYBANK", atm_strike, call_price, put_price, straddle_price,ltp)
                    price_history["banknifty_straddle"].append(straddle_price)


                if len(price_history["timestamps"]) > 100:
                    price_history["timestamps"].pop(0)
                    price_history["nifty_straddle"].pop(0)
                    price_history["sensex_straddle"].pop(0)
                    price_history["bankex_straddle"].pop(0)
                    price_history["finnifty_straddle"].pop(0)
                    price_history["midcapnifty_straddle"].pop(0)
                    price_history["banknifty_straddle"].pop(0)




                await self.send(json.dumps({
                    "timestamp": timestamp,
                    "nifty": {"atm_strike": nifty_data[0], "call_price": nifty_data[1], "put_price": nifty_data[2], "straddle_price": nifty_data[1] + nifty_data[2], "ltp": nifty_data[4] if nifty_data else None},
                    "sensex": {"atm_strike": sensex_data[0], "call_price": sensex_data[1], "put_price": sensex_data[2], "straddle_price": sensex_data[1] + sensex_data[2], "ltp": sensex_data[4] if sensex_data else None},
                    "bankex": {"atm_strike": bankex_data[0], "call_price": bankex_data[1], "put_price": bankex_data[2], "straddle_price": bankex_data[1] + bankex_data[2], "ltp": bankex_data[4] if bankex_data else None},
                    "finnifty": {"atm_strike": finnifty_data[0], "call_price": finnifty_data[1], "put_price": finnifty_data[2], "straddle_price": finnifty_data[1] + finnifty_data[2], "ltp": finnifty_data[4] if finnifty_data else None},
                    "midcapnifty": {"atm_strike": midcapnifty_data[0], "call_price": midcapnifty_data[1], "put_price": midcapnifty_data[2], "straddle_price": midcapnifty_data[1] + midcapnifty_data[2], "ltp": midcapnifty_data[4] if midcapnifty_data else None},
                    "banknifty": {"atm_strike": banknifty_data[0], "call_price": banknifty_data[1], "put_price": banknifty_data[2], "straddle_price": banknifty_data[1] + banknifty_data[2], "ltp": banknifty_data[4] if banknifty_data else None},
                }))

               
                await asyncio.sleep(10)
                # time.sleep(10)  # Use time.sleep() in a synchronous function


            except Exception as e:
                logging.error(f"WebSocket Error: {e}")
    
    def get_atm_straddle(self, index_type):
        try:
            symbol_map = {"NIFTY50": "NSE:NIFTY50-INDEX", "SENSEX": "BSE:SENSEX-INDEX","BANKEX":"BSE:BANKEX-INDEX","FINNIFTY":"NSE:FINNIFTY-INDEX","MIDCPNIFTY":"NSE:MIDCPNIFTY-INDEX","NIFTYBANK": "NSE:NIFTYBANK-INDEX"}
            symbol = symbol_map.get(index_type)
            if not symbol:
                logging.error("Invalid Index Type: %s", index_type)
                return None

            response = fyers.quotes({"symbols": symbol})
            if response.get("code") == 429:
                logging.warning("API Rate Limit Reached. Retrying after 10 seconds...")
                asyncio.run(asyncio.sleep(10))
                return self.get_atm_straddle(index_type)

            if not response or "d" not in response or not response["d"]:
                logging.error("Invalid API Response: %s", response)
                return None

            ltp = response["d"][0]["v"].get("lp")
            if ltp is None:
                logging.error("LTP not found in response")
                return None

            atm_strike = round(ltp / 50) * 50
            if index_type == "NIFTY50":

                expiry = self.nifty_get_today_expiry()
                base_symbol = "NIFTY"
                exchange = "NSE"
            elif index_type == "SENSEX":

                expiry = self.sensex_get_today_expiry()
                base_symbol = "SENSEX"
                exchange = "BSE"
            elif index_type == "BANKEX":

                expiry = self.BANKEX_get_today_expiry()
                base_symbol = "BANKEX"
                exchange = "BSE"
            elif index_type == "FINNIFTY":

                expiry = self.FINNIFTY_get_today_expiry()
                base_symbol = "FINNIFTY"
                exchange = "NSE"
            elif index_type == "MIDCPNIFTY":

                expiry = self.midcap_get_last_thursday_expiry()
                base_symbol = "MIDCPNIFTY"
                exchange = "NSE"
            elif index_type == "NIFTYBANK":

                expiry = self.banknifty_get_last_thursday_expiry()
                base_symbol = "NIFTYBANK"
                exchange = "NSE"
            else:
                logging.error("Invalid Index Type for Expiry Calculation")
                return None

            if not expiry:
                return None
            
            # base_symbol = "NIFTY" if index_type == "NIFTY50" else "SENSEX"
            if index_type == "NIFTY50":
                base_symbol = "NIFTY"
            elif index_type == "SENSEX":
                base_symbol = "SENSEX"
            elif index_type == "BANKEX":
                base_symbol = "BANKEX"
            elif index_type == "FINNIFTY":
                base_symbol = "FINNIFTY"
            elif index_type == "MIDCPNIFTY":
                base_symbol = "MIDCPNIFTY"
            elif index_type == "NIFTYBANK":
                base_symbol = "NIFTYBANK"
            

            

            
            atm_call_symbol = f"{exchange}:{base_symbol}{expiry}{atm_strike}CE"
            atm_put_symbol = f"{exchange}:{base_symbol}{expiry}{atm_strike}PE"
            print(atm_call_symbol,atm_put_symbol)

            response = fyers.quotes({"symbols": f"{atm_call_symbol},{atm_put_symbol}"})
            if response.get("code") == 429:
                logging.warning("API Rate Limit Reached. Retrying after 10 seconds...")
                asyncio.run(asyncio.sleep(10))
                return self.get_atm_straddle(index_type)

            if not response or "d" not in response:
                logging.error("Invalid Option Chain Response: %s", response)
                return None

            call_price, put_price = None, None
            for data in response["d"]:
                name = data.get("n", "")
                price = data["v"].get("lp", 0)
                if "CE" in name:
                    call_price = price
                elif "PE" in name:
                    put_price = price

            if call_price is None or put_price is None:
                logging.error("Failed to fetch option prices")
                return None

            return atm_strike, call_price, put_price,ltp

        except Exception as e:
            logging.error(f"API Error: {e}")
            return None

    def save_to_db(self, index_name, atm_strike, call_price, put_price, straddle_price,ltp):
        try:
            StraddlePrice.objects.create(
                index_name=index_name,
                atm_strike=atm_strike,
                call_price=call_price,
                put_price=put_price,
                straddle_price=straddle_price,
                ltp=ltp
            )
            logging.info(f"Data Saved: {index_name} | {atm_strike} | {call_price} | {put_price} | {straddle_price}|{ltp}")
        except Exception as e:
            logging.error(f"Database Save Error: {e}")

    def sensex_get_today_expiry(self):
        """Get the expiry date dynamically for every upcoming Tuesday."""
        today = datetime.date.today()
        # Calculate the number of days to the next Tuesday (weekday = 1 for Tuesday)
        days_until_tuesday = (1 - today.weekday()) % 7
        next_tuesday = today + datetime.timedelta(days=days_until_tuesday)

        # Format the expiry date as per Fyers' symbol format
        month_map = {
            1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 
            7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"
        }
        
        formatted_expiry = f"{next_tuesday.year % 100:02d}{month_map[next_tuesday.month]}{next_tuesday.day:02d}"
        logging.debug(f"Formatted Expiry: {formatted_expiry}")
        print(formatted_expiry)
        return formatted_expiry
    
    def nifty_get_today_expiry(self):
        """Get today's expiry date dynamically for NIFTY options."""
        today = datetime.date.today()
        weekday = today.weekday()

        # NIFTY Weekly Expiry on Thursday
        if weekday < 3:
            expiry = today + datetime.timedelta(days=(3 - weekday))
        elif weekday == 3:
            expiry = today
        else:
            expiry = today + datetime.timedelta(days=(7 - weekday + 3))

        # Format the expiry date as per Fyers' symbol format
        month_map = {
            1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 
            7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"
        }
        
        formatted_expiry = f"{expiry.year % 100:02d}{month_map[expiry.month]}{expiry.day:02d}"
        logging.debug(f"Formatted Expiry: {formatted_expiry}")
        return formatted_expiry
     
    def BANKEX_get_today_expiry(self):
        """Calculate the last Thursday expiry date of the current month."""
        today = datetime.date.today()
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if next_month == 1 else 0)
        first_day_next_month = datetime.date(next_year, next_month, 1)
        last_day_this_month = first_day_next_month - datetime.timedelta(days=1)
        
        while last_day_this_month.weekday() != 1:  # Thursday is weekday 3
            last_day_this_month -= datetime.timedelta(days=1)
        
        month_map = {
            1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 
            7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
        }
        print(f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}")
        return f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}"

    def FINNIFTY_get_today_expiry(self):
        """Calculate the last Thursday expiry date of the current month."""
        today = datetime.date.today()
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if next_month == 1 else 0)
        first_day_next_month = datetime.date(next_year, next_month, 1)
        last_day_this_month = first_day_next_month - datetime.timedelta(days=1)
        
        while last_day_this_month.weekday() != 3:  # Thursday is weekday 3
            last_day_this_month -= datetime.timedelta(days=1)
        
        month_map = {
            1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 
            7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
        }
        print(f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}")
        return f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}"
    
        
    def midcap_get_last_thursday_expiry(self):
        """Calculate the last Thursday expiry date of the current month."""
        today = datetime.date.today()
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if next_month == 1 else 0)
        first_day_next_month = datetime.date(next_year, next_month, 1)
        last_day_this_month = first_day_next_month - datetime.timedelta(days=1)
        
        while last_day_this_month.weekday() != 3:  # Thursday is weekday 3
            last_day_this_month -= datetime.timedelta(days=1)
        
        month_map = {
            1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 
            7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
        }
        print(f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}")
        return f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}"
    
    def banknifty_get_last_thursday_expiry(self):
        """Calculate the last Thursday expiry date of the current month."""
        today = datetime.date.today()
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if next_month == 1 else 0)
        first_day_next_month = datetime.date(next_year, next_month, 1)
        last_day_this_month = first_day_next_month - datetime.timedelta(days=1)
        
        while last_day_this_month.weekday() != 3:  # Thursday is weekday 3
            last_day_this_month -= datetime.timedelta(days=1)
        
        month_map = {
            1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 
            7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"
        }
        print(f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}")
        return f"{last_day_this_month.year % 100}{month_map[last_day_this_month.month]}"
    
