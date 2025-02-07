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

price_history = {"timestamps": [], "nifty_straddle": [], "sensex_straddle": []}

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
    # async def connect(self):
    #     self.symbol = self.scope["url_route"]["kwargs"]["symbol"]  # Get symbol from URL
    #     await self.accept()
    #     await self.send(text_data=json.dumps({"message": f"Connected to {self.symbol}"}))
    #     self.is_active = True

    #     asyncio.create_task(self.fetch_and_send_data())


    # async def disconnect(self, close_code):
    #     self.is_active = False
    #     logging.warning(f"WebSocket Disconnected. Close Code: {close_code}")


    #     print(f"Disconnected from {self.symbol}")

    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     await self.send(text_data=json.dumps({"message": f"Received: {data}"}))
    # # async def connect(self):
    # #     await self.accept()
    # #     logging.info("WebSocket Connection Established.")
    # #     self.is_active = True
    # #     asyncio.create_task(self.fetch_and_send_data())

    # # async def disconnect(self, close_code):
    # #     self.is_active = False
    # #     logging.warning(f"WebSocket Disconnected. Close Code: {close_code}")

    async def fetch_and_send_data(self):
        while self.is_active:
            try:
                nifty_data = await asyncio.to_thread(self.get_atm_straddle, "NIFTY50")
                sensex_data = await asyncio.to_thread(self.get_atm_straddle, "SENSEX")
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                if nifty_data:
                    atm_strike, call_price, put_price = nifty_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "NIFTY50", atm_strike, call_price, put_price, straddle_price)
                    price_history["timestamps"].append(timestamp)
                    price_history["nifty_straddle"].append(straddle_price)

                if sensex_data:
                    atm_strike, call_price, put_price = sensex_data
                    straddle_price = call_price + put_price
                    await asyncio.to_thread(self.save_to_db, "SENSEX", atm_strike, call_price, put_price, straddle_price)
                    price_history["sensex_straddle"].append(straddle_price)

                if len(price_history["timestamps"]) > 100:
                    price_history["timestamps"].pop(0)
                    price_history["nifty_straddle"].pop(0)
                    price_history["sensex_straddle"].pop(0)

                await self.send(json.dumps({
                    "timestamp": timestamp,
                    "nifty": {"atm_strike": nifty_data[0], "call_price": nifty_data[1], "put_price": nifty_data[2], "straddle_price": nifty_data[1] + nifty_data[2]} if nifty_data else None,
                    "sensex": {"atm_strike": sensex_data[0], "call_price": sensex_data[1], "put_price": sensex_data[2], "straddle_price": sensex_data[1] + sensex_data[2]} if sensex_data else None
                }))
                await asyncio.sleep(2)

            except Exception as e:
                logging.error(f"WebSocket Error: {e}")

    def get_atm_straddle(self, index_type):
        try:
            symbol_map = {"NIFTY50": "NSE:NIFTY50-INDEX", "SENSEX": "BSE:SENSEX-INDEX"}
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
            else:
                logging.error("Invalid Index Type for Expiry Calculation")
                return None

            if not expiry:
                return None
            
            base_symbol = "NIFTY" if index_type == "NIFTY50" else "SENSEX"
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

            return atm_strike, call_price, put_price

        except Exception as e:
            logging.error(f"API Error: {e}")
            return None

    def save_to_db(self, index_name, atm_strike, call_price, put_price, straddle_price):
        try:
            StraddlePrice.objects.create(
                index_name=index_name,
                atm_strike=atm_strike,
                call_price=call_price,
                put_price=put_price,
                straddle_price=straddle_price
            )
            logging.info(f"Data Saved: {index_name} | {atm_strike} | {call_price} | {put_price} | {straddle_price}")
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
     

     
