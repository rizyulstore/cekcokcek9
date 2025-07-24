"""
XL OTP Authentication Module
Handles OTP request and verification for XL accounts before package shooting
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
XL_OTP_API_CONFIG = {
    'api_key': '91e30218-7148-4ab8-bd84-a98c89fa2ba7',
    'otp_request_url': 'https://golang-openapi-reqotp-xltembakservice.kmsp-store.com/v1',
    'login_url': 'https://golang-openapi-login-xltembakservice.kmsp-store.com/v1'
}

class XLOTPManager:
    """Manages XL OTP authentication process"""
    
    def __init__(self):
        self.pending_otps = {}  # Store pending OTP sessions
        
    async def request_otp(self, phone_number: str) -> Dict[str, Any]:
        """
        Request OTP for XL phone number
        
        Args:
            phone_number (str): XL phone number (format: 628xxxxxxxxx)
            
        Returns:
            Dict: Response with status and auth_id if successful
        """
        try:
            # Validate phone number format
            if not phone_number.startswith('628') or len(phone_number) < 10:
                return {
                    'status': False,
                    'message': 'Format nomor tidak valid. Gunakan format 628xxxxxxxxx'
                }
            
            logger.info(f"Requesting OTP for phone: {phone_number}")
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'api_key': XL_OTP_API_CONFIG['api_key'],
                    'phone': phone_number,
                    'method': 'OTP'
                }
                
                async with session.get(XL_OTP_API_CONFIG['otp_request_url'], params=params) as response:
                    data = await response.json()
                    
                    if data.get('status') is True:
                        auth_id = data['data'].get('auth_id')
                        
                        # Store pending OTP session
                        self.pending_otps[phone_number] = {
                            'auth_id': auth_id,
                            'timestamp': datetime.now(),
                            'expires_at': datetime.now() + timedelta(minutes=5)
                        }
                        
                        logger.info(f"OTP requested successfully for {phone_number}")
                        return {
                            'status': True,
                            'message': f'OTP berhasil dikirim ke nomor {phone_number}',
                            'auth_id': auth_id
                        }
                    else:
                        logger.error(f"OTP request failed: {data.get('message', 'Unknown error')}")
                        return {
                            'status': False,
                            'message': data.get('message', 'Gagal mengirim OTP')
                        }
                        
        except Exception as e:
            logger.error(f"Error requesting OTP: {e}")
            return {
                'status': False,
                'message': f'Terjadi kesalahan: {str(e)}'
            }
    
    async def verify_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP code and get access token
        
        Args:
            phone_number (str): XL phone number
            otp_code (str): OTP code received via SMS
            
        Returns:
            Dict: Response with status and access_token if successful
        """
        try:
            # Check if there's a pending OTP session
            if phone_number not in self.pending_otps:
                return {
                    'status': False,
                    'message': 'Tidak ada permintaan OTP untuk nomor ini. Silakan minta OTP terlebih dahulu.'
                }
            
            otp_session = self.pending_otps[phone_number]
            
            # Check if OTP session has expired
            if datetime.now() > otp_session['expires_at']:
                del self.pending_otps[phone_number]
                return {
                    'status': False,
                    'message': 'OTP telah kedaluwarsa. Silakan minta OTP baru.'
                }
            
            auth_id = otp_session['auth_id']
            
            logger.info(f"Verifying OTP for phone: {phone_number}")
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'api_key': XL_OTP_API_CONFIG['api_key'],
                    'phone': phone_number,
                    'method': 'OTP',
                    'auth_id': auth_id,
                    'otp': otp_code
                }
                
                async with session.get(XL_OTP_API_CONFIG['login_url'], params=params) as response:
                    data = await response.json()
                    
                    if data.get('status') is True:
                        access_token = data['data'].get('access_token')
                        
                        # Clean up pending OTP session
                        del self.pending_otps[phone_number]
                        
                        logger.info(f"OTP verified successfully for {phone_number}")
                        return {
                            'status': True,
                            'message': 'OTP berhasil diverifikasi',
                            'access_token': access_token,
                            'phone_number': phone_number
                        }
                    else:
                        logger.error(f"OTP verification failed: {data.get('message', 'Unknown error')}")
                        return {
                            'status': False,
                            'message': data.get('message', 'Kode OTP tidak valid')
                        }
                        
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return {
                'status': False,
                'message': f'Terjadi kesalahan: {str(e)}'
            }
    
    def cleanup_expired_otps(self):
        """Clean up expired OTP sessions"""
        current_time = datetime.now()
        expired_phones = [
            phone for phone, session in self.pending_otps.items()
            if current_time > session['expires_at']
        ]
        
        for phone in expired_phones:
            del self.pending_otps[phone]
            logger.info(f"Cleaned up expired OTP session for {phone}")

# Global OTP manager instance
otp_manager = XLOTPManager()