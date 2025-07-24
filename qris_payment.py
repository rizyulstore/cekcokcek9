"""
QRIS Payment Integration for XL Package Manager
Handles QRIS generation and payment verification
"""

import requests
import logging
from typing import Optional, Dict, Any
import urllib3

# Disable SSL warnings for payment API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# QRIS Configuration
QRIS_BASE_QR_STRING = "00020101021126670016COM.NOBUBANK.WWW01189360050300000879140214528415756549050303UMI51440014ID.CO.QRIS.WWW0215ID20253753827490303UMI5204481253033605802ID5921RIZYULSTORE OK21885606005BOGOR61051611062070703A0163048CCF"

# Payment API Configuration
PAYMENT_API_CONFIG = {
    'base_url': 'https://qris.payment.web.id/payment/qris/OK2188560',
    'username': 'rizyul04',
    'token': '2188560:CTeEXHdL21rKv6OWRaSVUMi8A9oQn57D'
}

logger = logging.getLogger(__name__)

def calculate_crc16(data: bytes) -> int:
    """Calculate CRC16 checksum for QRIS"""
    polynomial = 0x1021
    crc = 0xFFFF
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    return crc

def generate_qr_string(amount: int) -> str:
    """
    Generate QRIS QR string with specified amount
    
    Args:
        amount (int): Payment amount in IDR
        
    Returns:
        str: Complete QRIS QR string
        
    Raises:
        ValueError: If QRIS format is invalid
    """
    try:
        # Remove checksum and modify version
        qris_base = QRIS_BASE_QR_STRING[:-4].replace("010211", "010212")
        
        # Create nominal tag
        nominal_str = str(amount)
        nominal_tag = f"54{len(nominal_str):02d}{nominal_str}"
        
        # Find insertion position
        insert_position = qris_base.find("5802ID")
        if insert_position == -1:
            raise ValueError("Format QRIS tidak valid, tidak ditemukan tag '5802ID'")
        
        # Insert nominal tag
        qris_with_nominal = qris_base[:insert_position] + nominal_tag + qris_base[insert_position:]
        
        # Calculate and append checksum
        checksum = format(calculate_crc16(qris_with_nominal.encode()), '04X')
        
        return qris_with_nominal + checksum
        
    except Exception as e:
        logger.error(f"Error generating QR string: {e}")
        raise ValueError(f"Gagal membuat QR code: {e}")

def check_payment(amount: int, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Check if payment with specified amount has been received
    
    Args:
        amount (int): Expected payment amount
        timeout (int): Request timeout in seconds
        
    Returns:
        Optional[Dict]: Payment data if found, None otherwise
    """
    url = PAYMENT_API_CONFIG['base_url']
    params = {
        "username": PAYMENT_API_CONFIG['username'],
        "token": PAYMENT_API_CONFIG['token']
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'XL-Package-Manager/1.0'
    }

    try:
        logger.info(f"Checking payment for amount: {amount}")
        # Disable SSL verification for this specific API with warning suppression
        with requests.Session() as session:
            session.verify = False
            response = session.get(url, params=params, headers=headers, timeout=timeout)

        if response.status_code != 200:
            logger.error(f"Payment API error: Status Code {response.status_code}")
            return None

        data = response.json()

        if data.get("status") == "success":
            transactions = data.get("data", [])
            logger.info(f"Retrieved {len(transactions)} transactions")
            
            for trx in transactions:
                try:
                    trx_amount = int(trx.get("amount", 0))
                    trx_type = trx.get("type", "")
                    
                    # Check if transaction matches our criteria
                    if trx_amount == amount and trx_type == "CR":
                        payment_data = {
                            "status": True,
                            "amount": trx_amount,
                            "issuer_reff": trx.get("issuer_reff", "-"),
                            "buyer_reff": trx.get("buyer_reff", "-"),
                            "timestamp": trx.get("datetime", ""),
                            "description": trx.get("description", "")
                        }
                        logger.info(f"Payment found: {payment_data}")
                        return payment_data
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid transaction data: {e}")
                    continue
                    
            logger.info(f"No matching payment found for amount: {amount}")
            return None
            
        else:
            logger.error(f"Payment API response error: {data}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Payment API request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected payment check error: {e}")
        return None

def validate_amount(amount: int) -> bool:
    """
    Validate payment amount
    
    Args:
        amount (int): Amount to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Minimum 10,000 IDR, Maximum 10,000,000 IDR
    return 10000 <= amount <= 10000000

def format_qris_amount(amount: int) -> str:
    """
    Format amount for display in QRIS
    
    Args:
        amount (int): Amount in IDR
        
    Returns:
        str: Formatted amount string
    """
    return f"Rp {amount:,}".replace(",", ".")

class QRISPaymentManager:
    """Manager class for QRIS payment operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_payment_qr(self, amount: int, reference: str = "") -> Dict[str, Any]:
        """
        Create QRIS payment QR code
        
        Args:
            amount (int): Payment amount
            reference (str): Payment reference/description
            
        Returns:
            Dict: QR code data and metadata
        """
        try:
            if not validate_amount(amount):
                raise ValueError("Jumlah pembayaran tidak valid")
            
            qr_string = generate_qr_string(amount)
            
            return {
                'success': True,
                'qr_string': qr_string,
                'amount': amount,
                'formatted_amount': format_qris_amount(amount),
                'reference': reference,
                'instructions': [
                    'Scan QR code dengan aplikasi mobile banking',
                    'Masukkan PIN untuk konfirmasi pembayaran',
                    'Tunggu notifikasi pembayaran berhasil',
                    'Saldo akan otomatis bertambah setelah pembayaran dikonfirmasi'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating payment QR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, amount: int, max_attempts: int = 5) -> Dict[str, Any]:
        """
        Verify payment with retry mechanism
        
        Args:
            amount (int): Expected payment amount
            max_attempts (int): Maximum verification attempts
            
        Returns:
            Dict: Verification result
        """
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Payment verification attempt {attempt + 1}/{max_attempts}")
                payment_data = check_payment(amount)
                
                if payment_data:
                    return {
                        'success': True,
                        'payment_data': payment_data,
                        'attempt': attempt + 1
                    }
                
            except Exception as e:
                self.logger.error(f"Payment verification error on attempt {attempt + 1}: {e}")
        
        return {
            'success': False,
            'error': 'Pembayaran tidak ditemukan setelah beberapa kali pengecekan'
        }