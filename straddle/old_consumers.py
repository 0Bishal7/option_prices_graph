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

# API Credentials
ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FYERS_CLIENT_ID")

if not ACCESS_TOKEN or not CLIENT_ID:
    raise ValueError("Missing Fyers API credentials. Check your .env file.")

# Initialize Fyers API
fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=ACCESS_TOKEN, is_async=False)

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Data Storage for Live Updates
price_history = {"timestamps": [], "straddle_prices": []}

class StraddleConsumer(AsyncWebsocketConsumer):
    """WebSocket Consumer for fetching ATM straddle prices."""

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
        """Fetch and send ATM straddle price data periodically."""
        while self.is_active:
            try:
                data = await asyncio.to_thread(self.get_atm_straddle)
                if data:
                    atm_strike, call_price, put_price = data
                    straddle_price = call_price + put_price
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                    # Save to Database
                    await asyncio.to_thread(self.save_to_db, atm_strike, call_price, put_price, straddle_price)

                    # Store for Plotting
                    price_history["timestamps"].append(timestamp)
                    price_history["straddle_prices"].append(straddle_price)

                    # Limit history size
                    if len(price_history["timestamps"]) > 100:
                        price_history["timestamps"].pop(0)
                        price_history["straddle_prices"].pop(0)

                    # Send Data via WebSocket
                    await self.send(json.dumps({
                        "timestamp": timestamp,
                        "atm_strike": atm_strike,
                        "call_price": call_price,
                        "put_price": put_price,
                        "straddle_price": straddle_price
                    }))

                await asyncio.sleep(2)  # Reduce API call frequency

            except Exception as e:
                logging.error(f"WebSocket Error: {e}")

    def get_atm_straddle(self):
        """Fetch the ATM straddle price from Fyers API."""
        try:
            symbol = "NSE:NIFTY50-INDEX"
            response = fyers.quotes({"symbols": symbol})

            logging.debug(f"Index Response: {response}")  # Debugging

            if response.get("code") == 429:
                logging.warning("API Rate Limit Reached. Retrying after 10 seconds...")
                asyncio.run(asyncio.sleep(10))  # Use asyncio sleep instead of time.sleep
                return self.get_atm_straddle()

            if not response or "d" not in response or not response["d"]:
                logging.error("Invalid API Response: %s", response)
                return None

            ltp = response["d"][0]["v"].get("lp")
            logging.debug(f"LTP: {ltp}")  # Debugging
            
            if ltp is None:
                logging.error("LTP not found in response")
                return None

            # Round to the nearest 50 to find ATM strike
            atm_strike = round(ltp / 50) * 50
            expiry = self.get_today_expiry()

            # Ensure expiry is in the correct format, and log it for debugging
            logging.debug(f"Expiry: {expiry}")  # Debugging
            atm_call_symbol = f"NSE:NIFTY{expiry}{atm_strike}CE"
            atm_put_symbol = f"NSE:NIFTY{expiry}{atm_strike}PE"

            logging.debug(f"ATM Call Symbol: {atm_call_symbol}")
            logging.debug(f"ATM Put Symbol: {atm_put_symbol}")

            # Fetching the options data using the correctly formatted symbols
            response = fyers.quotes({"symbols": f"{atm_call_symbol},{atm_put_symbol}"})

            logging.debug(f"Options Response: {response}")  # Debugging

            if response.get("code") == 429:
                logging.warning("API Rate Limit Reached. Retrying after 10 seconds...")
                asyncio.run(asyncio.sleep(10))  
                return self.get_atm_straddle()

            if not response or "d" not in response:
                logging.error("Invalid Option Chain Response: %s", response)
                return None

            call_price, put_price = None, None
            for data in response["d"]:
                name = data.get("n", "")
                price = data["v"].get("lp", 0)
                logging.debug(f"Option {name} Price: {price}")  # Debugging
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

    def save_to_db(self, atm_strike, call_price, put_price, straddle_price):
        """Save straddle price data to the database."""
        try:
            StraddlePrice.objects.create(
                atm_strike=atm_strike,
                call_price=call_price,
                put_price=put_price,
                straddle_price=straddle_price
            )
            logging.info(f"Data Saved: {atm_strike} | {call_price} | {put_price} | {straddle_price}")
        except Exception as e:
            logging.error(f"Database Save Error: {e}")

    def get_today_expiry(self):
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
     

     