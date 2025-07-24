import asyncio
import aiohttp
import logging
import os
from datetime import datetime, timedelta
from utils import format_currency, sensor_phone, format_datetime_wib
from flask import current_app

class TelegramNotifier:
    def __init__(self):
        self.settings = None
        self.load_settings()

    def load_settings(self):
        """Load settings from database"""
        try:
            from models import TelegramSettings
            from app import db

            self.settings = TelegramSettings.query.first()
            if not self.settings:
                # Create default settings
                self.settings = TelegramSettings()
                db.session.add(self.settings)
                db.session.commit()

        except Exception as e:
            logging.warning(f"Could not load Telegram settings from database: {str(e)}")
            # Fallback to environment variables
            self.settings = type('obj', (object,), {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'group_id': os.getenv('TELEGRAM_GROUP_ID'),
                'website_name': os.getenv('WEBSITE_NAME', 'XL Package Manager'),
                'website_url': os.getenv('WEBSITE_URL', 'https://yourwebsite.com'),
                'is_enabled': bool(os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_GROUP_ID')),
                'success_message_format': """⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
📆 Expired: {expired_date}
🔑 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Harga: {amount}""",
                'failed_message_format': """❌ Transaksi Portal Ke-{transaction_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔑 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Harga: {amount}
🔍 Error: {error_message}""",
                'topup_pending_message_format': """💰 Top-Up Portal Ke-{topup_count} PENDING
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

⏳ Status: Menunggu Konfirmasi
💰 Jumlah: {amount}""",
                'topup_success_message_format': """✅ Top-Up Portal Ke-{topup_count} BERHASIL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Jumlah: {amount}""",
                'topup_failed_message_format': """❌ Top-Up Portal Ke-{topup_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Jumlah: {amount}"""
            })()

    def update_settings(self, settings):
        """Update settings object"""
        self.settings = settings

    @property
    def enabled(self):
        return (self.settings and 
                self.settings.is_enabled and 
                self.settings.bot_token and 
                self.settings.group_id)

    async def send_message(self, message):
        """Send message to Telegram group"""
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.settings.bot_token}/sendMessage"
            data = {
                'chat_id': self.settings.group_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        logging.info("Telegram notification sent successfully")
                        return True
                    else:
                        logging.error(f"Failed to send Telegram notification: {response.status}")
                        return False

        except Exception as e:
            logging.error(f"Error sending Telegram notification: {str(e)}")
            return False

    async def send_success_notification(self, transaction, user, package):
        """Send success notification"""
        if not self.enabled:
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.filter_by(status='success').count()

            # Get transaction date
            transaction_date = transaction.created_at.strftime("%Y-%m-%d")

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Format message using template
            message = self.settings.success_message_format.format(
                transaction_count=transaction_count,
                username=user.username,
                phone=censored_phone,
                package_name=package.name,
                expired_date=transaction_date,
                website_name=self.settings.website_name,
                amount=format_currency(transaction.amount),
                trx_id=transaction.trx_id or 'N/A'
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending success notification: {str(e)}")
            return False

    async def send_failed_notification(self, transaction, user, package, error_message):
        """Send failed notification"""
        if not self.enabled:
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Format message using template
            message = self.settings.failed_message_format.format(
                transaction_count=transaction_count,
                username=user.username,
                phone=censored_phone,
                package_name=package.name,
                website_name=self.settings.website_name,
                amount=format_currency(transaction.amount),
                error_message=error_message,
                trx_id=transaction.trx_id or 'N/A'
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending failed notification: {str(e)}")
            return False

    async def send_processing_notification(self, transaction, user, package):
        """Send processing notification for QRIS/DANA payments"""
        if not self.enabled:
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Format message for processing status
            message = f"""⏳ Transaksi Portal Ke-{transaction_count} SEDANG DIPROSES
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📄 Transaksi: {package.name}
💳 Metode: {transaction.payment_method}
🔑 TRX ID: {transaction.trx_id or 'N/A'}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

⏳ Status: Menunggu Pembayaran
💰 Harga: {format_currency(transaction.amount)}"""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending processing notification: {str(e)}")
            return False

    async def send_cancelled_notification(self, transaction, user, package):
        """Send cancelled notification"""
        if not self.enabled:
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Format message for cancelled status
            message = f"""❌ Transaksi Portal Ke-{transaction_count} DIBATALKAN
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📄 Transaksi: {package.name}
💳 Metode: {transaction.payment_method}
🔑 TRX ID: {transaction.trx_id or 'N/A'}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

❌ Status: Dibatalkan
💰 Harga: {format_currency(transaction.amount)}"""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending cancelled notification: {str(e)}")
            return False

    async def send_topup_pending_notification(self, topup, user):
        """Send top-up pending notification"""
        if not self.enabled:
            return False

        try:
            # Get top-up count
            from models import TopUp
            topup_count = TopUp.query.count()

            # Get created date
            created_date = topup.created_at.strftime("%Y-%m-%d")

            # Format message using template
            message = self.settings.topup_pending_message_format.format(
                topup_count=topup_count,
                username=user.username,
                payment_method=topup.payment_method.upper(),
                created_date=created_date,
                website_name=self.settings.website_name,
                amount=format_currency(topup.amount)
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending top-up pending notification: {str(e)}")
            return False

    async def send_topup_success_notification(self, topup, user):
        """Send top-up success notification"""
        if not self.enabled:
            return False

        try:
            # Get top-up count
            from models import TopUp
            topup_count = TopUp.query.filter_by(status='completed').count()

            # Get created date
            created_date = topup.created_at.strftime("%Y-%m-%d")

            # Format message using template
            message = self.settings.topup_success_message_format.format(
                topup_count=topup_count,
                username=user.username,
                payment_method=topup.payment_method.upper(),
                created_date=created_date,
                website_name=self.settings.website_name,
                amount=format_currency(topup.amount)
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending top-up success notification: {str(e)}")
            return False

    async def send_topup_failed_notification(self, topup, user):
        """Send top-up failed notification"""
        if not self.enabled:
            return False

        try:
            # Get top-up count
            from models import TopUp
            topup_count = TopUp.query.count()

            # Get created date
            created_date = topup.created_at.strftime("%Y-%m-%d")

            # Format message using template
            message = self.settings.topup_failed_message_format.format(
                topup_count=topup_count,
                username=user.username,
                payment_method=topup.payment_method.upper(),
                created_date=created_date,
                website_name=self.settings.website_name,
                amount=format_currency(topup.amount)
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending top-up failed notification: {str(e)}")
            return False

    async def send_xut_success_notification(self, transaction, user, package, response_message, addon_name=None):
        """Send XUT-specific success notification"""
        if not self.enabled:
            logging.warning("Telegram notifications are disabled")
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.filter_by(status='success').count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Determine package name based on addon
            if addon_name:
                display_name = f"{package.name} + {addon_name}"
            else:
                display_name = package.name

            # Use configurable XUT success format with fallback
            if hasattr(self.settings, 'xut_success_message_format') and self.settings.xut_success_message_format:
                message = self.settings.xut_success_message_format.format(
                    transaction_count=transaction_count,
                    username=user.username,
                    phone=censored_phone,
                    package_name=display_name,
                    trx_id=transaction.trx_id or 'N/A',
                    website_name=self.settings.website_name,
                    amount=format_currency(transaction.amount),
                    response=response_message[:100] + ('...' if len(response_message) > 100 else '')
                )
            else:
                # Fallback message format
                message = f"""⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📄 Transaksi: {display_name}
🔢 TRX ID: {transaction.trx_id or 'N/A'}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

✅ Status: Berhasil
💰 Harga: {format_currency(transaction.amount)}
📱 Respon: {response_message[:100] + ('...' if len(response_message) > 100 else '')}"""

            logging.info(f"Sending XUT success notification: {message[:100]}...")
            result = await self.send_message(message)
            logging.info(f"XUT success notification sent: {result}")
            return result

        except Exception as e:
            logging.error(f"Error sending XUT success notification: {str(e)}")
            return False

    async def send_xut_failed_notification(self, transaction, user, package, error_message, addon_name):
        """Send XUT-specific failed notification for addon"""
        if not self.enabled:
            return False

        try:
            # Get transaction count
            from models import Transaction
            transaction_count = Transaction.query.count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Use configurable XUT failed format
            message = self.settings.xut_failed_message_format.format(
                transaction_count=transaction_count,
                username=user.username,
                phone=censored_phone,
                package_name=package.name,
                trx_id=transaction.trx_id or 'N/A',
                website_name=self.settings.website_name,
                addon_name=addon_name,
                amount=format_currency(transaction.amount),
                error_message=error_message
            )

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending XUT failed notification: {str(e)}")
            return False

    async def send_multiaddon_progress_notification(self, transaction, user, progress_message, current, total):
        """Send multi-addon progress notification"""
        if not self.enabled:
            return False

        try:
            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Progress notification format
            message = f"""⏳ PROGRESS MULTI-ADDON ({current}/{total})
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📦 Status: {progress_message}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

📊 Progress: {current}/{total} paket"""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending multi-addon progress notification: {str(e)}")
            return False

    async def send_multiaddon_success_notification(self, transaction, user, package, response_message, success_count, total_count):
        """Send multi-addon success notification with progress"""
        if not self.enabled:
            return False

        try:
            # Get transaction count (includes all types)
            from models import Transaction, MultiAddonTransaction
            transaction_count = Transaction.query.count() + MultiAddonTransaction.query.count()

            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Multi-addon success format with progress
            message = f"""✅ TRANSAKSI MULTI-ADDON SUKSES #{transaction_count} ({success_count}/{total_count})
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📦 Paket: {package.name} BYPASS
💰 Harga: {format_currency(package.get_price_for_user(user))}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

✅ Status: Berhasil ({success_count}/{total_count})
📱 Respon: {response_message[:100] + '...' if len(response_message) > 100 else response_message}"""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending multi-addon success notification: {str(e)}")
            return False

    async def send_multiaddon_failed_notification(self, transaction, user, package, error_message, failed_count, total_count):
        """Send multi-addon failed notification with progress"""
        if not self.enabled:
            return False

        try:
            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Multi-addon failed format with progress
            message = f"""❌ TRANSAKSI MULTI-ADDON GAGAL ({failed_count}/{total_count})
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📦 Paket: {package.name} BYPASS
💰 Harga: {format_currency(package.get_price_for_user(user))}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

❌ Status: Gagal ({failed_count}/{total_count})
🔍 Error: {error_message[:200] + '...' if len(error_message) > 200 else error_message}"""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending multi-addon failed notification: {str(e)}")
            return False

    async def send_multiaddon_summary_notification(self, transaction, user, successful, failed, total):
        """Send multi-addon final summary notification"""
        if not self.enabled:
            return False

        try:
            # Censor phone number
            censored_phone = sensor_phone(transaction.phone_number)

            # Determine status emoji and message
            if successful == total:
                status_emoji = "✅"
                status_text = "SEMUA BERHASIL"
            elif successful > 0:
                status_emoji = "⚠️"
                status_text = "SEBAGIAN BERHASIL"
            else:
                status_emoji = "❌"
                status_text = "SEMUA GAGAL"

            # Summary notification format
            message = f"""{status_emoji} RINGKASAN MULTI-ADDON {status_text}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {user.username}
💼 Nomer: {censored_phone}
📦 Total Paket: {total}
✅ Berhasil: {successful}
❌ Gagal: {failed}
💰 Total Biaya: {format_currency(transaction.total_amount)}
━━━━━━━━━━━━━━━━━
💎 Official Website: {self.settings.website_name}

🏁 Proses selesai! Terima kasih telah menggunakan layanan kami."""

            return await self.send_message(message)

        except Exception as e:
            logging.error(f"Error sending multi-addon summary notification: {str(e)}")
            return False

    async def send_test_message(self, test_message):
        """Send test message"""
        return await self.send_message(test_message)

# Global instance
telegram_notifier = TelegramNotifier()