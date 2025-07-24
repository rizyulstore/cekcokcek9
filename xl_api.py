# Applying the provided changes to the original code to include the transaction status check method.
import asyncio
import aiohttp
import logging
import os
import time
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

class XLAPIManager:
    def __init__(self):
        self.api_key = os.environ.get("XL_API_KEY", "91e30218-7148-4ab8-bd84-a98c89fa2ba7")
        self.dor_api_key = os.environ.get("DOR_API_KEY", "0a1ccba4-e6fc-498c-af2f-5f889c765aaa")
        self.base_urls = {
            'token_list': 'https://golang-openapi-accesstokenlist-xltembakservice.kmsp-store.com/v1',
            'login': 'https://golang-openapi-login-xltembakservice.kmsp-store.com/v1',
            'extend_token': 'https://golang-openapi-login-xltembakservice.kmsp-store.com/v1',
            'packages': 'https://golang-openapi-paketaktif-xltembakservice.kmsp-store.com/v1',
            'purchase': 'https://golang-openapi-tembakpaket-xltembakservice.kmsp-store.com/v1',
            'package_purchase': 'https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1'
        }

    async def get_valid_token(self, phone_number: str, user=None) -> Optional[str]:
        """Get valid token for XL account"""
        try:
            # First check if user has stored token
            if user and user.xl_token and user.xl_verified:
                # Check if token is still valid (less than 1 hour old)
                if user.xl_token_time and (time.time() - user.xl_token_time) < 3600:
                    return user.xl_token

            # Get token from API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_urls['token_list'],
                    params={"api_key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") and data.get("data"):
                            for token_data in data["data"]:
                                if token_data.get("msisdn") == phone_number:
                                    return token_data.get("token")

            return None

        except Exception as e:
            logging.error(f"Error getting valid token: {str(e)}")
            return None

    async def login_xl_account(self, user, phone_number: str) -> Tuple[bool, str]:
        """Login to XL account and get token"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "phone": phone_number,
                    "method": "LOGIN_BY_ACCESS_TOKEN"
                }

                async with session.get(self.base_urls['login'], params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status"):
                            token = data.get("data", {}).get("token")
                            if token:
                                return True, token
                            else:
                                return False, "No token received"
                        else:
                            return False, data.get("message", "Login failed")
                    else:
                        return False, f"HTTP Error: {resp.status}"

        except Exception as e:
            logging.error(f"XL login error: {str(e)}")
            return False, str(e)

    async def extend_token(self, phone: str, session_id: str, token: str) -> Optional[str]:
        """Extend XL token validity"""
        try:
            auth_id = f"{session_id}:{token}"
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "phone": phone,
                    "method": "LOGIN_BY_ACCESS_TOKEN",
                    "auth_id": auth_id
                }

                async with session.get(self.base_urls['extend_token'], params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status"):
                            return data.get("data", {}).get("token")

            return None

        except Exception as e:
            logging.error(f"Token extend error: {str(e)}")
            return None

    async def get_active_packages(self, phone_number: str, token: str) -> Tuple[bool, Any]:
        """Get active packages for XL number"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "msisdn": phone_number,
                    "token": token
                }

                async with session.get(self.base_urls['packages'], params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status"):
                            return True, data.get("data", [])
                        else:
                            return False, data.get("message", "Failed to get packages")
                    else:
                        return False, f"HTTP Error: {resp.status}"

        except Exception as e:
            logging.error(f"Get packages error: {str(e)}")
            return False, str(e)

    async def purchase_package(self, user, phone_number: str, package_code: str, payment_method: str = 'PULSA') -> Tuple[bool, Dict[str, Any]]:
        """Purchase XL package using specified payment method"""
        try:
            logging.info(f"Starting package purchase: phone={phone_number}, package={package_code}, payment_method={payment_method}")
            # Use user's stored XL token from OTP verification
            token = user.xl_token if user and user.xl_otp_verified else None
            if not token:
                # Fallback to get_valid_token if no stored token
                token = await self.get_valid_token(phone_number, user)
                if not token:
                    return False, {"error": "No valid token available. Please verify OTP first."}

            async with aiohttp.ClientSession() as session:
                # Create base parameters
                params = {
                    "api_key": self.api_key,
                    "phone": phone_number,
                    "access_token": token,
                    "package_code": package_code
                }

                # Add payment_method parameter only for non-PULSA methods
                if payment_method != 'PULSA':
                    params["payment_method"] = payment_method

                logging.info(f"Calling API: {self.base_urls['package_purchase']} with params: {params}")
                logging.info(f"Using payment method: {payment_method}")

                async with session.get(self.base_urls['package_purchase'], params=params) as resp:
                    response_text = await resp.text()
                    logging.info(f"API Response Status: {resp.status}, Body: {response_text}")

                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            logging.info(f"Parsed JSON response: {data}")

                            if data.get("status"):
                                result = {
                                    "success": True,
                                    "reference": data.get("data", {}).get("reference", ""),
                                    "trx_id": data.get("data", {}).get("trx_id", ""),
                                    "message": data.get("message", "Success")
                                }
                                logging.info(f"Purchase successful: {result}")
                                return True, result
                            else:
                                error_msg = data.get("message", "Purchase failed")
                                logging.error(f"Purchase failed: {error_msg}")
                                # For XUT packages, return the full message to check for 422
                                return False, {"error": error_msg, "message": error_msg}
                        except Exception as json_err:
                            logging.error(f"Failed to parse JSON response: {json_err}")
                            return False, {"error": f"Invalid response format: {response_text}"}
                    else:
                        logging.error(f"HTTP Error {resp.status}: {response_text}")
                        return False, {"error": f"HTTP Error: {resp.status}"}

        except Exception as e:
            logging.error(f"Purchase package error: {str(e)}")
            return False, {"error": str(e)}

    async def check_quota(self, token: str) -> Tuple[bool, Any]:
        """Check XL quota information using quota details API"""
        try:
            async with aiohttp.ClientSession() as session:
                url_kuota = "https://golang-openapi-quotadetails-xltembakservice.kmsp-store.com/v1"
                params = {
                    "api_key": self.api_key,
                    "access_token": token
                }

                async with session.get(url_kuota, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logging.info(f"Quota data: {data}")

                        if data.get("status") and data.get("statusCode") == 200:
                            quotas = data.get("data", {}).get("quotas", [])
                            return True, quotas
                        else:
                            return False, data.get("message", "Failed to get quota data")
                    else:
                        return False, f"HTTP Error: {resp.status}"

        except Exception as e:
            logging.error(f"Check quota error: {str(e)}")
            return False, str(e)

    async def purchase_package_qris(self, user, phone_number, package_code):
        """Purchase package using QRIS payment method"""
        try:
            if not user.xl_token:
                return False, {'error': 'XL token not found'}

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_urls['package_purchase']}"
                params = {
                    "api_key": self.api_key,
                    "package_code": package_code,
                    "phone": phone_number,
                    "access_token": user.xl_token,
                    "payment_method": "QRIS"
                }

                logging.info(f"Requesting QRIS package purchase: {params}")

                async with session.get(url, params=params) as response:
                    result = await response.json()
                    logging.info(f"QRIS API Response: {result}")

                    if result.get("status"):
                        return True, result
                    else:
                        return False, {'error': result.get('message', 'Unknown error')}

        except Exception as e:
            logging.error(f"QRIS Package purchase error: {str(e)}")
            return False, {'error': str(e)}

    async def purchase_package_dana(self, user, phone_number: str, package_code: str):
        """Purchase package using DANA payment method"""
        try:
            if not user.xl_token:
                return False, {"error": "XL token not found. Please login first."}

            params = {
                "api_key": self.api_key,
                "package_code": package_code,
                "phone": phone_number,
                "access_token": user.xl_token,
                "payment_method": "DANA"
            }

            logging.info(f"Requesting DANA package purchase: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_urls['package_purchase'], params=params) as response:
                    result = await response.json()

            logging.info(f"DANA API Response: {result}")

            if result.get("status"):
                return True, result
            else:
                error_msg = result.get("message", "Unknown error")
                return False, {"error": error_msg}

        except Exception as e:
            logging.error(f"DANA purchase error: {str(e)}")
            return False, {"error": f"Request failed: {str(e)}"}

    async def check_transaction_status(self, trx_id: str):
        """Check transaction status by transaction ID"""
        try:
            check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
            params = {
                "api_key": self.api_key,
                "trx_id": trx_id
            }

            logging.info(f"Checking transaction status: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(check_url, params=params) as response:
                    result = await response.json()

            logging.info(f"Transaction status check response: {result}")

            if result.get("status"):
                return True, result
            else:
                error_msg = result.get("message", "Transaction check failed")
                return False, {"error": error_msg}

        except Exception as e:
            logging.error(f"Transaction status check error: {str(e)}")
            return False, {"error": f"Request failed: {str(e)}"}