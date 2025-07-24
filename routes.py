from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import asyncio
import logging

from app import db
from models import User, Package, Transaction, TopUp, UserRole, SystemSettings
from forms import (RegistrationForm, LoginForm, PackageForm, PurchaseForm,
                   TopUpForm, UserEditForm, BalanceAdjustForm, XLLoginForm,
                   XLOTPRequestForm, XLOTPVerifyForm)
from xl_api import XLAPIManager
from xl_otp import otp_manager
from utils import format_currency, format_phone, is_valid_phone
from telegram_notifier import telegram_notifier

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    phone=form.phone.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(
                url_for('main.dashboard'))
        flash('Invalid username/password or account is inactive.', 'error')
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics for all users (both admin and regular users)
    total_transactions = Transaction.query.count()
    success_transactions = Transaction.query.filter_by(
        status='success').count()

    if current_user.is_admin():
        # For admin: show all transactions (recent 10)
        recent_transactions = Transaction.query.order_by(Transaction.created_at.desc())\
                                              .limit(10).all()
        all_user_transactions = None
    else:
        # For regular users: show only their transactions
        recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                               .order_by(Transaction.created_at.desc())\
                                               .limit(5).all()

        # Get all user transactions (not just current user) for members
        all_user_transactions = Transaction.query.order_by(Transaction.created_at.desc())\
                                                .limit(10).all()

    return render_template('dashboard.html',
                           recent_transactions=recent_transactions,
                           all_user_transactions=all_user_transactions,
                           total_transactions=total_transactions,
                           success_transactions=success_transactions)


@bp.route('/health')
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


# Admin Routes
@bp.route('/admin/packages')
@login_required
def admin_packages():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    packages = Package.query.all()
    return render_template('admin/packages.html', packages=packages)


@bp.route('/admin/packages/add', methods=['GET', 'POST'])
@login_required
def admin_add_package():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Handle form submission directly from POST data
        payment_methods = request.form.getlist('payment_methods')
        if not payment_methods:
            payment_methods = ['PULSA']  # Default to PULSA if none selected

        package = Package(
            name=request.form.get('name'),
            code=request.form.get('code'),
            price_member=float(request.form.get('price_member', 0)),
            price_reseller=float(request.form.get('price_reseller', 0)),
            api_code=request.form.get('api_code'),
            package_ewallet=request.form.get('package_ewallet'),
            payment_methods=','.join(payment_methods),
            is_active=bool(request.form.get('is_active')))
        db.session.add(package)
        db.session.commit()
        flash('Package added successfully!', 'success')
        return redirect(url_for('main.admin_packages'))

    form = PackageForm()
    packages = Package.query.all()
    return render_template('admin/packages.html',
                           form=form,
                           packages=packages,
                           action='add')


@bp.route('/admin/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(package_id)

    if request.method == 'POST':
        # Handle form submission directly from POST data
        payment_methods = request.form.getlist('payment_methods')
        if not payment_methods:
            payment_methods = ['PULSA']  # Default to PULSA if none selected

        package.name = request.form.get('name')
        package.code = request.form.get('code')
        package.price_member = float(request.form.get('price_member', 0))
        package.price_reseller = float(request.form.get('price_reseller', 0))
        package.api_code = request.form.get('api_code')
        package.package_ewallet = request.form.get('package_ewallet')
        package.payment_methods = ','.join(payment_methods)
        package.is_active = bool(request.form.get('is_active'))
        db.session.commit()
        flash('Package updated successfully!', 'success')
        return redirect(url_for('main.admin_packages'))

    form = PackageForm(obj=package)
    # Set current payment methods for the form
    if package.payment_methods:
        form.payment_methods.data = package.get_enabled_payment_methods()
    packages = Package.query.all()
    return render_template('admin/packages.html',
                           form=form,
                           packages=packages,
                           package=package,
                           action='edit')


@bp.route('/admin/packages/delete/<int:package_id>')
@login_required
def admin_delete_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    flash('Package deleted successfully!', 'success')
    return redirect(url_for('main.admin_packages'))


@bp.route('/admin/members')
@login_required
def admin_members():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/members.html', users=users)


@bp.route('/admin/members/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_member(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.role = UserRole(form.role.data)
        user.balance = form.balance.data
        user.is_active = form.is_active.data
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('main.admin_members'))

    return render_template('admin/members.html',
                           form=form,
                           user=user,
                           action='edit')


@bp.route('/admin/balance')
@login_required
def admin_balance():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    users = User.query.filter(User.role != UserRole.ADMIN).all()
    return render_template('admin/balance.html', users=users)


@bp.route('/admin/balance/adjust', methods=['POST'])
@login_required
def admin_adjust_balance():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    form = BalanceAdjustForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        if form.action.data == 'add':
            user.balance += form.amount.data
        else:
            user.balance -= form.amount.data
            if user.balance < 0:
                user.balance = 0

        db.session.commit()
        flash(
            f'Balance {form.action.data}ed successfully for {user.username}!',
            'success')

    return redirect(url_for('main.admin_balance'))


@bp.route('/admin/telegram-settings', methods=['GET', 'POST'])
@login_required
def admin_telegram_settings():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import TelegramSettings
    from forms import TelegramSettingsForm

    # Get or create telegram settings
    settings = TelegramSettings.query.first()
    if not settings:
        settings = TelegramSettings()
        db.session.add(settings)
        db.session.commit()

    form = TelegramSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.bot_token = form.bot_token.data
        settings.group_id = form.group_id.data
        settings.website_name = form.website_name.data
        settings.website_url = form.website_url.data
        settings.success_message_format = form.success_message_format.data
        settings.failed_message_format = form.failed_message_format.data
        settings.topup_pending_message_format = form.topup_pending_message_format.data
        settings.topup_success_message_format = form.topup_success_message_format.data
        settings.topup_failed_message_format = form.topup_failed_message_format.data
        settings.xut_success_message_format = form.xut_success_message_format.data
        settings.xut_failed_message_format = form.xut_failed_message_format.data
        settings.is_enabled = form.is_enabled.data
        settings.updated_at = datetime.utcnow()

        db.session.commit()

        # Update telegram notifier with new settings
        telegram_notifier.update_settings(settings)

        flash('Pengaturan Telegram berhasil disimpan!', 'success')
        return redirect(url_for('main.admin_telegram_settings'))

    return render_template('admin/telegram_settings.html',
                           form=form,
                           settings=settings)


@bp.route('/admin/telegram-settings/test', methods=['POST'])
@login_required
def admin_test_telegram():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    # Check CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception:
        flash('Invalid CSRF token', 'error')
        return redirect(url_for('main.admin_telegram_settings'))

    from models import TelegramSettings

    settings = TelegramSettings.query.first()
    if not settings or not settings.bot_token or not settings.group_id:
        flash('Bot Token dan Group ID harus diisi terlebih dahulu!', 'error')
        return redirect(url_for('main.admin_telegram_settings'))

    try:
        # Test message
        test_message = f"""🧪 **TEST NOTIFICATION**
━━━━━━━━━━━━━━━━━
📅 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB
👤 Admin: {current_user.username}
💻 Website: {settings.website_name}
━━━━━━━━━━━━━━━━━
✅ Konfigurasi Telegram berhasil!"""

        # Send test notification
        import asyncio
        result = asyncio.run(telegram_notifier.send_test_message(test_message))

        if result:
            flash('Pesan test berhasil dikirim ke grup Telegram!', 'success')
        else:
            flash('Gagal mengirim pesan test. Periksa Bot Token dan Group ID.',
                  'error')

    except Exception as e:
        logging.error(f"Test telegram error: {str(e)}")
        flash(f'Gagal mengirim pesan test: {str(e)}', 'error')

    return redirect(url_for('main.admin_telegram_settings'))


@bp.route('/admin/website-settings', methods=['GET', 'POST'])
@login_required
def admin_website_settings():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import WebsiteSettings
    from forms import WebsiteSettingsForm

    # Get or create website settings
    settings = WebsiteSettings.get_settings()
    form = WebsiteSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.site_title = form.site_title.data
        settings.site_description = form.site_description.data
        settings.logo_url = form.logo_url.data
        settings.favicon_url = form.favicon_url.data
        settings.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Website settings saved successfully!', 'success')
        return redirect(url_for('main.admin_website_settings'))

    return render_template('admin/website_settings.html',
                           form=form,
                           settings=settings)


@bp.route('/admin/payment-methods', methods=['GET', 'POST'])
@login_required
def admin_payment_methods():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import PaymentMethodSettings
    from forms import PaymentMethodSettingsForm

    # Get or create payment method settings
    settings = PaymentMethodSettings.query.first()
    if not settings:
        settings = PaymentMethodSettings()
        db.session.add(settings)
        db.session.commit()

    form = PaymentMethodSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.pulsa_enabled = form.pulsa_enabled.data
        settings.dana_enabled = form.dana_enabled.data
        settings.qris_enabled = form.qris_enabled.data
        settings.updated_at = datetime.utcnow()

        # Ensure at least one method is enabled
        if not (settings.pulsa_enabled or settings.dana_enabled
                or settings.qris_enabled):
            settings.pulsa_enabled = True
            flash(
                'At least one payment method must be enabled. PULSA has been enabled.',
                'warning')

        db.session.commit()
        flash('Payment method settings saved successfully!', 'success')
        return redirect(url_for('main.admin_payment_methods'))

    return render_template('admin/payment_methods.html',
                           form=form,
                           settings=settings)


@bp.route('/admin/xut-packages')
@login_required
def admin_xut_packages():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    # Get XUT packages (XUTP and XUTS)
    xut_packages = Package.query.filter(
        Package.package_ewallet.in_(['PREMIUMXC', 'SUPERXC'])).all()

    return render_template('admin/xut_packages.html',
                           xut_packages=xut_packages)


@bp.route('/admin/xut-packages/add', methods=['POST'])
@login_required
def admin_add_xut_package():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        name = request.form.get('name')
        xut_type = request.form.get('xut_type')
        price_member = float(request.form.get('price_member', 0))
        price_reseller = float(request.form.get('price_reseller', 0))
        addon_price_member = float(request.form.get('addon_price_member',
                                                    6000))
        addon_price_reseller = float(
            request.form.get('addon_price_reseller', 6000))
        is_active = bool(request.form.get('is_active'))

        # Set API code and package_ewallet based on XUT type
        if xut_type == 'PREMIUMXC':
            api_code = 'XLUNLITURBOPREMIUMXC_PULSA'
            package_ewallet = 'PREMIUMXC'
            code = 'XUTP'
        elif xut_type == 'SUPERXC':
            api_code = 'XLUNLITURBOSUPERXC_PULSA'
            package_ewallet = 'SUPERXC'
            code = 'XUTS'
        else:
            flash('Invalid XUT type selected.', 'error')
            return redirect(url_for('main.admin_xut_packages'))

        # Check if package already exists
        existing_package = Package.query.filter_by(
            package_ewallet=package_ewallet).first()
        if existing_package:
            flash(f'XUT package with type {xut_type} already exists.', 'error')
            return redirect(url_for('main.admin_xut_packages'))

        package = Package(
            name=name,
            code=code,
            price_member=price_member,
            price_reseller=price_reseller,
            addon_price_member=addon_price_member,
            addon_price_reseller=addon_price_reseller,
            api_code=api_code,
            package_ewallet=package_ewallet,
            payment_methods='PULSA',  # XUT packages use PULSA only
            is_active=is_active)

        db.session.add(package)
        db.session.commit()
        flash('XUT package added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding XUT package: {str(e)}")
        flash('Error adding XUT package. Please try again.', 'error')

    return redirect(url_for('main.admin_xut_packages'))


@bp.route('/admin/xut-packages/edit/<int:package_id>', methods=['POST'])
@login_required
def admin_edit_xut_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(package_id)

    # Ensure this is an XUT package
    if package.package_ewallet not in ['PREMIUMXC', 'SUPERXC']:
        flash('This is not an XUT package.', 'error')
        return redirect(url_for('main.admin_xut_packages'))

    try:
        name = request.form.get('name')
        xut_type = request.form.get('xut_type')
        price_member = float(request.form.get('price_member', 0))
        price_reseller = float(request.form.get('price_reseller', 0))
        addon_price_member = float(request.form.get('addon_price_member',
                                                    6000))
        addon_price_reseller = float(
            request.form.get('addon_price_reseller', 6000))
        is_active = bool(request.form.get('is_active'))

        # Set API code and package_ewallet based on XUT type
        if xut_type == 'PREMIUMXC':
            api_code = 'XLUNLITURBOPREMIUMXC_PULSA'
            package_ewallet = 'PREMIUMXC'
            code = 'XUTP'
        elif xut_type == 'SUPERXC':
            api_code = 'XLUNLITURBOSUPERXC_PULSA'
            package_ewallet = 'SUPERXC'
            code = 'XUTS'
        else:
            flash('Invalid XUT type selected.', 'error')
            return redirect(url_for('main.admin_xut_packages'))

        # Check if changing to existing package type
        if package.package_ewallet != package_ewallet:
            existing_package = Package.query.filter(
                Package.package_ewallet == package_ewallet, Package.id
                != package_id).first()
            if existing_package:
                flash(f'XUT package with type {xut_type} already exists.',
                      'error')
                return redirect(url_for('main.admin_xut_packages'))

        package.name = name
        package.code = code
        package.price_member = price_member
        package.price_reseller = price_reseller
        package.addon_price_member = addon_price_member
        package.addon_price_reseller = addon_price_reseller
        package.api_code = api_code
        package.package_ewallet = package_ewallet
        package.is_active = is_active

        db.session.commit()
        flash('XUT package updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating XUT package: {str(e)}")
        flash('Error updating XUT package. Please try again.', 'error')

    return redirect(url_for('main.admin_xut_packages'))


@bp.route('/admin/xut-packages/delete/<int:package_id>')
@login_required
def admin_delete_xut_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(package_id)

    # Ensure this is an XUT package
    if package.package_ewallet not in ['PREMIUMXC', 'SUPERXC']:
        flash('This is not an XUT package.', 'error')
        return redirect(url_for('main.admin_xut_packages'))

    try:
        db.session.delete(package)
        db.session.commit()
        flash('XUT package deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting XUT package: {str(e)}")
        flash('Error deleting XUT package. Please try again.', 'error')

    return redirect(url_for('main.admin_xut_packages'))

@bp.route('/admin/multiaddon-packages')
@login_required
def admin_multiaddon_packages():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import MultiAddonPackage
    packages = MultiAddonPackage.query.all()
    return render_template('admin/multiaddon_packages.html', packages=packages)

@bp.route('/admin/multiaddon-packages/add', methods=['POST'])
@login_required
def admin_add_multiaddon_package():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        from models import MultiAddonPackage
        
        name = request.form.get('name')
        package_code = request.form.get('package_code')
        api_code = request.form.get('api_code')
        price_member = float(request.form.get('price_member', 1000))
        price_reseller = float(request.form.get('price_reseller', 500))
        is_active = bool(request.form.get('is_active'))

        # Check if package already exists
        existing_package = MultiAddonPackage.query.filter_by(package_code=package_code).first()
        if existing_package:
            flash(f'Multi-addon package with code {package_code} already exists.', 'error')
            return redirect(url_for('main.admin_multiaddon_packages'))

        package = MultiAddonPackage(
            name=name,
            package_code=package_code,
            api_code=api_code,
            price_member=price_member,
            price_reseller=price_reseller,
            is_active=is_active
        )

        db.session.add(package)
        db.session.commit()
        flash('Multi-addon package added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding multi-addon package: {str(e)}")
        flash('Error adding multi-addon package. Please try again.', 'error')

    return redirect(url_for('main.admin_multiaddon_packages'))

@bp.route('/admin/multiaddon-packages/edit/<int:package_id>', methods=['POST'])
@login_required
def admin_edit_multiaddon_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import MultiAddonPackage
    package = MultiAddonPackage.query.get_or_404(package_id)

    try:
        name = request.form.get('name')
        package_code = request.form.get('package_code')
        api_code = request.form.get('api_code')
        price_member = float(request.form.get('price_member', 1000))
        price_reseller = float(request.form.get('price_reseller', 500))
        is_active = bool(request.form.get('is_active'))

        # Check if package code is unique (excluding current package)
        existing_package = MultiAddonPackage.query.filter(
            MultiAddonPackage.package_code == package_code,
            MultiAddonPackage.id != package_id
        ).first()
        
        if existing_package:
            flash(f'Multi-addon package with code {package_code} already exists.', 'error')
            return redirect(url_for('main.admin_multiaddon_packages'))

        package.name = name
        package.package_code = package_code
        package.api_code = api_code
        package.price_member = price_member
        package.price_reseller = price_reseller
        package.is_active = is_active

        db.session.commit()
        flash('Multi-addon package updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating multi-addon package: {str(e)}")
        flash('Error updating multi-addon package. Please try again.', 'error')

    return redirect(url_for('main.admin_multiaddon_packages'))

@bp.route('/admin/multiaddon-packages/delete/<int:package_id>')
@login_required
def admin_delete_multiaddon_package(package_id):
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    from models import MultiAddonPackage
    package = MultiAddonPackage.query.get_or_404(package_id)

    try:
        db.session.delete(package)
        db.session.commit()
        flash('Multi-addon package deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting multi-addon package: {str(e)}")
        flash('Error deleting multi-addon package. Please try again.', 'error')

    return redirect(url_for('main.admin_multiaddon_packages'))


@bp.route('/admin/transactions')
@login_required
def admin_transactions():
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.dashboard'))

    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    user_filter = request.args.get('user', '')

    query = Transaction.query

    # Apply filters
    if status_filter:
        query = query.filter(Transaction.status == status_filter)

    if user_filter:
        query = query.join(User).filter(User.username.contains(user_filter))

    transactions = query.order_by(Transaction.created_at.desc())\
                       .paginate(page=page, per_page=20, error_out=False)

    # Get statistics
    total_transactions = Transaction.query.count()
    success_transactions = Transaction.query.filter_by(
        status='success').count()
    failed_transactions = Transaction.query.filter_by(status='failed').count()
    total_revenue = db.session.query(db.func.sum(Transaction.amount))\
                             .filter(Transaction.status == 'success').scalar() or 0

    return render_template('admin/transactions.html',
                           transactions=transactions,
                           total_transactions=total_transactions,
                           success_transactions=success_transactions,
                           failed_transactions=failed_transactions,
                           total_revenue=total_revenue,
                           status_filter=status_filter,
                           user_filter=user_filter)


# Member/Reseller Routes
@bp.route('/packages')
@login_required
def packages():
    packages = Package.query.filter_by(is_active=True).all()
    return render_template('member/packages.html', packages=packages)


@bp.route('/packages/xut')
@login_required
def xut_packages():
    """Display XUT packages (XUTP/XUTS) with combo selection"""
    # Get main packages (XUTP and XUTS) - first try with package_ewallet
    main_packages = Package.query.filter(
        Package.package_ewallet.in_(['PREMIUMXC', 'SUPERXC']),
        Package.is_active == True).all()

    # If no packages found with package_ewallet, try with api_code as fallback
    if not main_packages:
        main_packages = Package.query.filter(
            Package.api_code.in_(
                ['XLUNLITURBOPREMIUMXC_PULSA', 'XLUNLITURBOSUPERXC_PULSA']),
            Package.is_active == True).all()

    # Get addon packages (XCS and XC 1+1 GB)
    addon_packages = Package.query.filter(
        Package.api_code.in_(
            ['bdb392a7aa12b21851960b7e7d54af2c', 'XL_XC1PLUS1DISC_PULSA']),
        Package.is_active == True).all()

    # All packages for JavaScript
    all_packages = main_packages + addon_packages

    # Debug info for admin
    if current_user.is_admin():
        all_packages_debug = Package.query.filter(
            Package.is_active == True).all()
        logging.info(
            f"Debug XUT packages - Main: {len(main_packages)}, Addon: {len(addon_packages)}, All active: {len(all_packages_debug)}"
        )

    return render_template('member/xut_packages.html',
                           main_packages=main_packages,
                           addon_packages=addon_packages,
                           all_packages=all_packages)


@bp.route('/packages/xut/purchase', methods=['POST'])
@login_required
def purchase_xut_package():
    """Purchase XUT package combo with sequential processing and 422 validation"""
    if not current_user.xl_otp_verified:
        flash('❌ Verifikasi OTP XL diperlukan untuk membeli paket!', 'error')
        return redirect(url_for('main.xl_otp_request'))

    try:
        main_package_id = request.form.get('main_package')
        phone_number = request.form.get('phone_number')
        payment_method = request.form.get('payment_method', 'PULSA')

        if not main_package_id or not phone_number:
            flash('Data tidak lengkap. Silakan coba lagi.', 'error')
            return redirect(url_for('main.xut_packages'))

        # Get main package
        main_package = Package.query.get_or_404(main_package_id)

        # Determine packages to process based on selection
        if main_package.package_ewallet == 'PREMIUMXC':
            # XUTP: Process XLUNLITURBOPREMIUMXC_PULSA then bdb392a7aa12b21851960b7e7d54af2c
            main_api_code = "XLUNLITURBOPREMIUMXC_PULSA"
            addon_api_code = "bdb392a7aa12b21851960b7e7d54af2c"
            package_name = "XUT Premium (XUTP)"
            addon_name = "XCS 8GB"  # Ubah teks ini sesuai keinginan
        elif main_package.package_ewallet == 'SUPERXC':
            # XUTS: Process XLUNLITURBOSUPERXC_PULSA then XL_XC1PLUS1DISC_PULSA
            main_api_code = "XLUNLITURBOSUPERXC_PULSA"
            addon_api_code = "XL_XC1PLUS1DISC_PULSA"
            package_name = "XUT Super (XUTS)"
            addon_name = "XC 1GB"  # Ubah teks ini sesuai keinginan
        else:
            flash('❌ Paket tidak valid.', 'error')
            return redirect(url_for('main.xut_packages'))

        # Calculate total price: main package + addon (dynamic pricing)
        main_price = main_package.get_price_for_user(current_user)
        addon_price = main_package.get_addon_price_for_user(current_user)
        total_price = main_price + addon_price

        # Check user balance
        if current_user.balance < total_price:
            flash('❌ Saldo tidak mencukupi. Silakan top up terlebih dahulu.',
                  'error')
            return redirect(url_for('main.topup'))

        def is_successful(code: str, message: str) -> bool:
            """Check if response indicates success based on package code"""
            if not message:
                return False

            msg = message.lower()
            logging.info(
                f"Checking success for {code} with message: {message[:100]}..."
            )

            if code in [
                    "XLUNLITURBOPREMIUMXC_PULSA", "XLUNLITURBOSUPERXC_PULSA"
            ]:
                # For XUT main packages, 422 error code indicates success
                has_422 = ("422" in msg or "error message: 422" in msg
                           or "status code:422" in msg)
                logging.info(f"XUT main package {code} - 422 found: {has_422}")
                return has_422
            elif code in [
                    "XL_XC1PLUS1DISC_PULSA", "bdb392a7aa12b21851960b7e7d54af2c"
            ]:
                # For addon packages, only success messages indicate success
                # Do NOT wait for 422 code, if it fails just mark as failed
                success_indicators = [
                    "paket berhasil dibeli", "berhasil", "sukses", "success",
                    "statuscode\":200", "status\":true"
                ]
                for indicator in success_indicators:
                    if indicator in msg.replace(" ", ""):
                        logging.info(
                            f"Addon package {code} - success indicator found: {indicator}"
                        )
                        return True
                logging.info(
                    f"Addon package {code} - no success indicators found")
                return False

            # Default fallback
            return "422" in msg

        # Process main package first
        from utils import generate_package_trx_id
        main_trx_id = generate_package_trx_id()

        main_transaction = Transaction(user_id=current_user.id,
                                       package_id=main_package.id,
                                       phone_number=phone_number,
                                       amount=main_price,
                                       status='processing',
                                       payment_method=payment_method,
                                       trx_id=main_trx_id)
        db.session.add(main_transaction)
        db.session.flush()

        xl_api = XLAPIManager()

        # Process main package with retry until 422 response
        main_success = False
        max_attempts = 10  # Maximum attempts to prevent infinite loop
        attempt = 0

        logging.info(
            f"Starting main package purchase: {main_api_code} for {phone_number}"
        )

        while not main_success and attempt < max_attempts:
            attempt += 1
            logging.info(f"Main package attempt {attempt}: {main_api_code}")

            try:
                success, result = asyncio.run(xl_api.purchase_package(current_user, phone_number,
                                            main_api_code, payment_method))

                response_message = result.get('message', '') if isinstance(
                    result, dict) else str(result)
                logging.info(f"Main package response: {response_message}")

                # For XUT main packages, check for 422 error code in the message
                # This indicates success for XLUNLITURBOPREMIUMXC_PULSA and XLUNLITURBOSUPERXC_PULSA
                is_422_success = False
                if main_api_code in [
                        "XLUNLITURBOPREMIUMXC_PULSA",
                        "XLUNLITURBOSUPERXC_PULSA"
                ]:
                    msg_lower = response_message.lower()
                    is_422_success = ("422" in msg_lower
                                      or "error message: 422" in msg_lower
                                      or "status code:422" in msg_lower)
                    logging.info(
                        f"Checking for 422 success - message contains 422: {is_422_success}"
                    )

                if success or is_422_success:
                    main_success = True
                    main_transaction.status = 'success'
                    main_transaction.reference = result.get(
                        'reference', '') if isinstance(result, dict) else ''
                    main_transaction.completed_at = datetime.utcnow()
                    logging.info(
                        f"Main package success on attempt {attempt} (422 detected as success: {is_422_success})"
                    )
                    break
                else:
                    logging.info(
                        f"Main package attempt {attempt} failed, waiting 35 seconds..."
                    )
                    if attempt < max_attempts:
                        import time
                        time.sleep(35)  # Wait 35 seconds before retry

            except Exception as e:
                logging.error(
                    f"Main package attempt {attempt} error: {str(e)}")
                if attempt < max_attempts:
                    import time
                    time.sleep(35)

        if not main_success:
            main_transaction.status = 'failed'
            main_transaction.error_message = f'Failed after {max_attempts} attempts'
            db.session.commit()
            flash(
                f'❌ Gagal memproses paket utama {package_name} setelah {max_attempts} percobaan.',
                'error')
            return redirect(url_for('main.dashboard'))

        # Deduct balance for main package
        current_user.balance -= main_price
        current_user.counted += 1

        # Process addon package - NO RETRY, single attempt only
        addon_trx_id = generate_package_trx_id()
        addon_transaction = Transaction(
            user_id=current_user.id,
            package_id=main_package.id,  # Use same package ID for tracking
            phone_number=phone_number,
            amount=addon_price,
            status='processing',
            payment_method=payment_method,
            trx_id=addon_trx_id)
        db.session.add(addon_transaction)
        db.session.flush()

        logging.info(
            f"Starting addon package purchase (single attempt): {addon_api_code} for {phone_number}"
        )

        try:
            # Single API call for addon package - no retry loop
            success, result = asyncio.run(xl_api.purchase_package(current_user, phone_number,
                                        addon_api_code, payment_method))

            response_message = result.get('message', '') if isinstance(
                result, dict) else str(result)
            logging.info(f"Addon package single response: {response_message}")

            # Check if addon package was successful based on response keywords
            addon_success_indicators = [
                "paket berhasil dibeli", "berhasil", "sukses", "success",
                "statuscode\":200", "status\":true"
            ]

            response_lower = response_message.lower().replace(" ", "")
            addon_is_successful = any(
                indicator in response_lower
                for indicator in addon_success_indicators)

            if success or addon_is_successful:
                # Addon package successful
                addon_transaction.status = 'success'
                addon_transaction.reference = result.get(
                    'reference', '') if isinstance(result, dict) else ''
                addon_transaction.completed_at = datetime.utcnow()

                # Deduct balance for addon
                current_user.balance -= addon_price
                current_user.counted += 1

                logging.info(
                    "Addon package purchase successful - transaction completed"
                )

                # Send XUT success notifications for both packages
                if telegram_notifier.enabled:
                    try:
                        # Send XUT success notification for main package
                        asyncio.create_task(telegram_notifier.send_xut_success_notification(
                            main_transaction, current_user, main_package, 
                            "Paket utama berhasil diaktivasi", None))
                        logging.info("XUT success notification sent for main package")
                        
                        # Send XUT success notification for addon package
                        asyncio.create_task(telegram_notifier.send_xut_success_notification(
                            addon_transaction, current_user, main_package,
                            "Add-on berhasil diaktivasi", addon_name))
                        logging.info("XUT success notification sent for addon package")
                    except Exception as e:
                        logging.error(
                            f"Failed to send XUT success notification: {str(e)}")

                flash(
                    f'✅ Paket {package_name} berhasil dibeli! Paket utama dan add-on telah diaktivasi.',
                    'success')
            else:
                # Addon failed - complete transaction immediately as failed
                addon_transaction.status = 'failed'
                addon_transaction.error_message = response_message
                addon_transaction.completed_at = datetime.utcnow()
                logging.error(
                    f"Addon package failed - transaction completed as failed: {response_message}"
                )

                # Send XUT notifications for partial success
                if telegram_notifier.enabled:
                    try:
                        # Send XUT success notification for main package
                        asyncio.create_task(telegram_notifier.send_xut_success_notification(
                            main_transaction, current_user, main_package,
                            "Paket utama berhasil diaktivasi", None))
                        logging.info("XUT success notification sent for main package")
                        
                        # Send XUT failed notification for addon package
                        asyncio.create_task(telegram_notifier.send_xut_failed_notification(
                            addon_transaction, current_user, main_package,
                            response_message, addon_name))
                        logging.info("XUT failed notification sent for addon package")
                    except Exception as e:
                        logging.error(
                            f"Failed to send XUT notifications: {str(e)}")

                flash(
                    f'⚠️ Paket utama {package_name} berhasil, tetapi {addon_name} gagal diaktivasi.',
                    'warning')

        except Exception as e:
            # Addon error - complete transaction immediately as failed
            addon_transaction.status = 'failed'
            addon_transaction.error_message = str(e)
            addon_transaction.completed_at = datetime.utcnow()
            logging.error(
                f"Addon package error - transaction completed as failed: {str(e)}"
            )

            # Send XUT notifications for addon error
            if telegram_notifier.enabled:
                try:
                    # Send XUT success notification for main package
                    asyncio.create_task(telegram_notifier.send_xut_success_notification(
                        main_transaction, current_user, main_package,
                        "Paket utama berhasil diaktivasi", None))
                    logging.info("XUT success notification sent for main package")
                    
                    # Send XUT failed notification for addon package
                    asyncio.create_task(telegram_notifier.send_xut_failed_notification(
                        addon_transaction, current_user, main_package,
                        str(e), addon_name))
                    logging.info("XUT failed notification sent for addon package")
                except Exception as notif_error:
                    logging.error(
                        f"Failed to send XUT notifications: {str(notif_error)}")

            flash(
                f'⚠️ Paket utama {package_name} berhasil, tetapi {addon_name} gagal diaktivasi.',
                'warning')

        db.session.commit()
        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback()
        logging.error(f"XUT combo purchase error: {str(e)}")
        flash('❌ Terjadi kesalahan saat membeli paket. Silakan coba lagi.',
              'error')
        return redirect(url_for('main.xut_packages'))


@bp.route('/packages/purchase', methods=['POST'])
@login_required
def purchase_package():
    form = PurchaseForm()
    if form.validate_on_submit():
        package = Package.query.get_or_404(form.package_id.data)
        phone_number = form.phone_number.data
        payment_method = form.payment_method.data

        # Check user balance
        package_price = package.get_price_for_user(current_user)
        if current_user.balance < package_price:
            flash('Insufficient balance. Please top up your account.', 'error')
            return redirect(url_for('main.packages'))

        try:
            # Get appropriate package code based on payment method
            package_code = package.get_package_code_for_payment(payment_method)

            # Generate TRX ID
            from utils import generate_package_trx_id
            trx_id = generate_package_trx_id()

            # Create transaction record
            transaction = Transaction(user_id=current_user.id,
                                      package_id=package.id,
                                      phone_number=phone_number,
                                      amount=package_price,
                                      status='processing',
                                      payment_method=payment_method,
                                      trx_id=trx_id)
            db.session.add(transaction)
            db.session.commit()

            # Handle different payment methods
            if payment_method == 'PULSA':
                # Process PULSA purchase directly
                xl_api = XLAPIManager()
                success, result = asyncio.run(
                    xl_api.purchase_package(current_user, phone_number,
                                            package_code, payment_method))

                if success:
                    # Deduct balance and update transaction
                    current_user.balance -= package_price
                    current_user.counted += 1
                    transaction.status = 'success'
                    transaction.reference = result.get('reference', '')
                    transaction.trx_id = result.get('trx_id', '')
                    transaction.completed_at = datetime.utcnow()

                    db.session.commit()

                    # Send Telegram notification
                    if telegram_notifier.enabled:
                        asyncio.create_task(
                            telegram_notifier.send_success_notification(
                                transaction, current_user, package))

                    flash('Package purchased successfully!', 'success')
                    return redirect(url_for('main.dashboard'))
                else:
                    # Update transaction as failed
                    transaction.status = 'failed'
                    transaction.error_message = result.get(
                        'error', 'Unknown error')
                    db.session.commit()

                    error_msg = result.get('error', 'Purchase failed')
                    flash(f'Purchase failed: {error_msg}', 'error')
                    return redirect(url_for('main.packages'))

            elif payment_method == 'QRIS':
                # Redirect to QRIS payment page
                session['pending_transaction_id'] = transaction.id
                return redirect(
                    url_for('main.package_qris_payment',
                            transaction_id=transaction.id))

            elif payment_method == 'DANA':
                # Redirect to DANA payment page
                session['pending_transaction_id'] = transaction.id
                return redirect(
                    url_for('main.package_dana_payment',
                            transaction_id=transaction.id))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Purchase error: {str(e)}")
            flash('An error occurred during purchase. Please try again.',
                  'error')
            return redirect(url_for('main.packages'))

    flash('Invalid form data.', 'error')
    return redirect(url_for('main.packages'))


@bp.route('/profile')
@login_required
def profile():
    form = XLLoginForm()
    return render_template('member/profile.html', form=form)


@bp.route('/profile/xl-login', methods=['POST'])
@login_required
def xl_login():
    form = XLLoginForm()
    if form.validate_on_submit():
        try:
            xl_api = XLAPIManager()
            success, token = asyncio.run(
                xl_api.login_xl_account(current_user, form.phone_number.data))

            if success:
                current_user.xl_phone = form.phone_number.data
                current_user.xl_token = token
                current_user.xl_verified = True
                current_user.xl_token_time = datetime.utcnow().timestamp()
                db.session.commit()
                flash('XL account connected successfully!', 'success')
            else:
                flash(f'XL login failed: {token}', 'error')

        except Exception as e:
            logging.error(f"XL login error: {str(e)}")
            flash('XL login failed due to system error.', 'error')

    return redirect(url_for('main.profile'))


# XL OTP Authentication Routes
@bp.route('/xl-otp', methods=['GET', 'POST'])
@login_required
def xl_otp_request():
    """Request OTP for XL authentication"""
    form = XLOTPRequestForm()

    if request.method == 'POST' and form.validate_on_submit():
        phone_number = form.xl_phone_number.data.strip()

        # Format phone number to ensure it starts with 628
        if phone_number.startswith('08'):
            phone_number = '628' + phone_number[2:]
        elif phone_number.startswith('8'):
            phone_number = '628' + phone_number[1:]
        elif not phone_number.startswith('628'):
            flash('Format nomor tidak valid. Gunakan format 628xxxxxxxxx',
                  'error')
            return render_template('member/xl_otp_request.html', form=form)

        try:
            # Request OTP using async manager
            result = asyncio.run(otp_manager.request_otp(phone_number))

            if result['status']:
                # Store phone in session for verification step
                current_user.xl_phone = phone_number
                db.session.commit()
                flash(result['message'], 'success')
                return redirect(url_for('main.xl_otp_verify'))
            else:
                flash(result['message'], 'error')

        except Exception as e:
            logging.error(f"OTP request error: {str(e)}")
            flash('Terjadi kesalahan saat meminta OTP. Silakan coba lagi.',
                  'error')

    return render_template('member/xl_otp_request.html', form=form)


@bp.route('/xl-otp/verify', methods=['GET', 'POST'])
@login_required
def xl_otp_verify():
    """Verify OTP code and complete authentication"""
    if not current_user.xl_phone:
        flash('Silakan minta OTP terlebih dahulu.', 'error')
        return redirect(url_for('main.xl_otp_request'))

    form = XLOTPVerifyForm()

    if request.method == 'POST' and form.validate_on_submit():
        otp_code = form.otp_code.data.strip()
        phone_number = current_user.xl_phone

        try:
            # Verify OTP using async manager
            result = asyncio.run(otp_manager.verify_otp(
                phone_number, otp_code))

            if result['status']:
                # Update user with verified XL account info
                current_user.xl_phone = phone_number
                current_user.xl_token = result['access_token']
                current_user.xl_verified = True
                current_user.xl_otp_verified = True
                current_user.xl_last_otp_time = datetime.utcnow()
                current_user.xl_token_time = datetime.utcnow().timestamp()

                db.session.commit()

                flash(
                    '✅ OTP berhasil diverifikasi! Akun XL Anda sudah terhubung.',
                    'success')
                return redirect(url_for('main.packages'))
            else:
                flash(result['message'], 'error')

        except Exception as e:
            logging.error(f"OTP verification error: {str(e)}")
            flash('Terjadi kesalahan saat verifikasi OTP. Silakan coba lagi.',
                  'error')

    return render_template('member/xl_otp_verify.html',
                           form=form,
                           phone=current_user.xl_phone)


@bp.route('/xl-otp/reset')
@login_required
def xl_otp_reset():
    """Reset XL OTP verification status"""
    current_user.xl_phone = None
    current_user.xl_token = None
    current_user.xl_verified = False
    current_user.xl_otp_verified = False
    current_user.xl_last_otp_time = None
    current_user.xl_token_time = None

    db.session.commit()
    flash('Verifikasi XL direset. Silakan verifikasi ulang.', 'info')
    return redirect(url_for('main.xl_otp_request'))


@bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                  .order_by(Transaction.created_at.desc())\
                                  .paginate(page=page, per_page=20, error_out=False)
    return render_template('member/history.html', transactions=transactions)


@bp.route('/payment/qris/<int:transaction_id>')
@login_required
def package_qris_payment(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.packages'))

    # Check if transaction is still pending
    if transaction.status != 'processing':
        flash('Transaction is no longer pending.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(transaction.package_id)

    try:
        # Get QRIS payment info from XL API
        xl_api = XLAPIManager()
        package_code = package.get_package_code_for_payment('QRIS')
        success, result = asyncio.run(
            xl_api.purchase_package_qris(current_user,
                                         transaction.phone_number,
                                         package_code))

        if success and 'data' in result:
            api_data = result['data']

            # Process QRIS data from API response
            qris_info = api_data.get('qris_data', {})
            qr_string = qris_info.get('qr_code', '')
            expired_time = qris_info.get('payment_expired_at', 0)
            remaining_time = 600  # 10 menit dalam detik

            # Format expired time in WIB
            from datetime import datetime, timedelta
            import pytz

            # Buat waktu expired 10 menit dari sekarang dalam WIB
            wib = pytz.timezone('Asia/Jakarta')
            current_time_wib = datetime.now(wib)
            expired_datetime_wib = current_time_wib + timedelta(minutes=10)
            expired_time_str = expired_datetime_wib.strftime('%H:%M:%S')

            # Format amount
            formatted_amount = f"Rp {transaction.amount:,.0f}".replace(
                ',', '.')

            # Create structured QRIS data for template
            qr_data = {
                'qr_string':
                qr_string,
                'formatted_amount':
                formatted_amount,
                'expired_time':
                expired_time_str,
                'remaining_time':
                remaining_time,
                'trx_id':
                api_data.get('trx_id', ''),
                'package_name':
                api_data.get('package_name', package.name),
                'instructions': [
                    'Buka aplikasi mobile banking atau e-wallet Anda',
                    'Pilih menu "Scan QR" atau "QRIS"',
                    'Scan QR code yang ditampilkan di layar',
                    'Periksa detail pembayaran dan konfirmasi',
                    'Masukkan PIN untuk menyelesaikan pembayaran',
                    'Tunggu notifikasi pembayaran berhasil'
                ]
            }

            # Update transaction with TRX ID
            if api_data.get('trx_id'):
                transaction.trx_id = api_data.get('trx_id')
                db.session.commit()

            return render_template('member/package_qris_payment.html',
                                   transaction=transaction,
                                   package=package,
                                   qr_data=qr_data,
                                   transaction_id=transaction.id,
                                   phone=transaction.phone_number)
        else:
            error_msg = result.get(
                'message', 'Failed to generate QRIS payment') if isinstance(
                    result, dict) else 'Failed to generate QRIS payment'
            flash(f'Failed to generate QRIS payment: {error_msg}', 'error')
            return redirect(url_for('main.packages'))

    except Exception as e:
        logging.error(f"QRIS payment error: {str(e)}")
        flash('Error generating QRIS payment.', 'error')
        return redirect(url_for('main.packages'))


@bp.route('/payment/qris/confirm/<int:transaction_id>', methods=['POST'])
@login_required
def confirm_package_qris_payment(transaction_id):
    """Manual confirmation for QRIS payment"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Skip if already processed
    if transaction.status != 'processing':
        return jsonify({
            'success': True,
            'status': transaction.status,
            'redirect': url_for('main.dashboard')
        })

    try:
        # Process payment confirmation
        package = Package.query.get(transaction.package_id)
        package_price = package.get_price_for_user(current_user)

        # Check if user has enough balance
        if current_user.balance < package_price:
            return jsonify({
                'success': False,
                'error': 'Saldo tidak mencukupi'
            })

        # Deduct balance and update transaction
        current_user.balance -= package_price
        current_user.counted += 1
        transaction.status = 'success'
        transaction.completed_at = datetime.utcnow()

        db.session.commit()

        # Send Telegram notification if enabled
        if telegram_notifier.enabled:
            try:
                asyncio.run(
                    telegram_notifier.send_success_notification(
                        transaction, current_user, package))
            except Exception as e:
                logging.error(f"Failed to send success notification: {str(e)}")

        return jsonify({
            'success': True,
            'status': 'completed',
            'message':
            f'Pembayaran dikonfirmasi! Paket telah dikirim ke {transaction.phone_number}',
            'redirect': url_for('main.dashboard')
        })

    except Exception as e:
        logging.error(f"QRIS payment confirmation error: {str(e)}")
        return jsonify({
            'success':
            False,
            'error':
            'Terjadi kesalahan saat mengkonfirmasi pembayaran'
        })


@bp.route('/payment/qris/cancel/<int:transaction_id>')
@login_required
def cancel_package_qris_payment(transaction_id):
    """Cancel QRIS payment for package purchase"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    if transaction.status == 'processing':
        transaction.status = 'cancelled'
        db.session.commit()
        flash('Pembayaran QRIS dibatalkan', 'info')

        # Send Telegram notification for cancellation
        if telegram_notifier.enabled:
            try:
                asyncio.create_task(
                    telegram_notifier.send_failed_notification(
                        transaction, current_user, package,
                        "Pembayaran QRIS dibatalkan oleh user."))
            except Exception as e:
                logging.error(f"Failed to send failed notification: {str(e)}")

    return redirect(url_for('main.packages'))


@bp.route('/payment/dana/<int:transaction_id>')
@login_required
def package_dana_payment(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.packages'))

    # Check if transaction is still pending
    if transaction.status != 'processing':
        flash('Transaction is no longer pending.', 'error')
        return redirect(url_for('main.dashboard'))

    package = Package.query.get_or_404(transaction.package_id)

    try:
        # Get DANA payment info from XL API
        xl_api = XLAPIManager()
        package_code = package.get_package_code_for_payment('DANA')
        success, result = asyncio.run(
            xl_api.purchase_package_dana(current_user,
                                         transaction.phone_number,
                                         package_code))

        if success and 'data' in result:
            dana_data = result['data']

            # Add expiry time in WIB (10 minutes from now)
            from datetime import datetime, timedelta
            import pytz

            wib = pytz.timezone('Asia/Jakarta')
            current_time_wib = datetime.now(wib)
            expired_datetime_wib = current_time_wib + timedelta(minutes=10)
            dana_data['expired_time_wib'] = expired_datetime_wib.strftime(
                '%H:%M:%S')
            dana_data['remaining_time'] = 600  # 10 minutes in seconds

            return render_template('member/package_dana_payment.html',
                                   transaction=transaction,
                                   package=package,
                                   dana_data=dana_data,
                                   transaction_id=transaction.id)
        else:
            flash('Failed to generate DANA payment. Please try again.',
                  'error')
            return redirect(url_for('main.packages'))

    except Exception as e:
        logging.error(f"DANA payment error: {str(e)}")
        flash('Error generating DANA payment.', 'error')
        return redirect(url_for('main.packages'))


@bp.route('/payment/dana/confirm/<int:transaction_id>', methods=['POST'])
@login_required
def confirm_package_dana_payment(transaction_id):
    """Manual confirmation for DANA payment"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Skip if already processed
    if transaction.status != 'processing':
        return jsonify({
            'success': True,
            'status': transaction.status,
            'redirect': url_for('main.dashboard')
        })

    try:
        # Process payment confirmation
        package = Package.query.get(transaction.package_id)
        package_price = package.get_price_for_user(current_user)

        # Check if user has enough balance
        if current_user.balance < package_price:
            return jsonify({
                'success': False,
                'error': 'Saldo tidak mencukupi'
            })

        # Deduct balance and update transaction
        current_user.balance -= package_price
        current_user.counted += 1
        transaction.status = 'success'
        transaction.completed_at = datetime.utcnow()

        db.session.commit()

        # Send Telegram notification if enabled
        if telegram_notifier.enabled:
            try:
                asyncio.run(
                    telegram_notifier.send_success_notification(
                        transaction, current_user, package))
            except Exception as e:
                logging.error(f"Failed to send success notification: {str(e)}")

        return jsonify({
            'success': True,
            'status': 'completed',
            'message':
            f'Pembayaran dikonfirmasi! Paket telah dikirim ke {transaction.phone_number}',
            'redirect': url_for('main.dashboard')
        })

    except Exception as e:
        logging.error(f"DANA payment confirmation error: {str(e)}")
        return jsonify({
            'success':
            False,
            'error':
            'Terjadi kesalahan saat mengkonfirmasi pembayaran'
        })


@bp.route('/payment/dana/cancel/<int:transaction_id>')
@login_required
def cancel_package_dana_payment(transaction_id):
    """Cancel DANA payment for package purchase"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Check if transaction belongs to current user
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    if transaction.status == 'processing':
        transaction.status = 'cancelled'
        db.session.commit()
        flash('Pembayaran DANA dibatalkan', 'info')

        # Send Telegram notification for cancellation
        if telegram_notifier.enabled:
            try:
                asyncio.create_task(
                    telegram_notifier.send_failed_notification(
                        transaction, current_user, package,
                        "Pembayaran DANA dibatalkan oleh user."))
            except Exception as e:
                logging.error(f"Failed to send failed notification: {str(e)}")

    return redirect(url_for('main.packages'))


@bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    form = TopUpForm()
    if form.validate_on_submit():
        if form.payment_method.data == 'qris':
            # Handle QRIS payment
            return redirect(
                url_for('main.topup_qris', amount=int(form.amount.data)))
        else:
            # Handle bank transfer (existing logic)
            topup_request = TopUp(user_id=current_user.id,
                                  amount=form.amount.data,
                                  payment_method=form.payment_method.data,
                                  status='pending')
            db.session.add(topup_request)
            db.session.commit()

            # Send Telegram notification for pending top-up
            if telegram_notifier.enabled:
                try:
                    asyncio.create_task(
                        telegram_notifier.send_topup_pending_notification(
                            topup_request, current_user))
                except Exception as e:
                    logging.error(
                        f"Failed to send top-up pending notification: {str(e)}"
                    )

            flash('Top-up request created! Please wait for admin approval.',
                  'info')
            return redirect(url_for('main.dashboard'))

    recent_topups = TopUp.query.filter_by(user_id=current_user.id)\
                              .order_by(TopUp.created_at.desc())\
                              .limit(10).all()

    return render_template('member/topup.html',
                           form=form,
                           recent_topups=recent_topups)


@bp.route('/topup/qris/<int:amount>')
@login_required
def topup_qris(amount):
    """Display QRIS payment page"""
    from qris_payment import QRISPaymentManager

    if not (10000 <= amount <= 10000000):
        flash('Invalid amount for QRIS payment', 'error')
        return redirect(url_for('main.topup'))

    qris_manager = QRISPaymentManager()
    qr_data = qris_manager.create_payment_qr(
        amount, f"Top-up for {current_user.username}")

    if not qr_data['success']:
        flash(f'Error creating QRIS: {qr_data["error"]}', 'error')
        return redirect(url_for('main.topup'))

    # Create pending topup record
    topup_request = TopUp(user_id=current_user.id,
                          amount=amount,
                          payment_method='qris',
                          status='pending')
    db.session.add(topup_request)
    db.session.commit()

    # Send Telegram notification for pending QRIS top-up
    if telegram_notifier.enabled:
        try:
            asyncio.create_task(
                telegram_notifier.send_topup_pending_notification(
                    topup_request, current_user))
        except Exception as e:
            logging.error(
                f"Failed to send top-up pending notification: {str(e)}")

    return render_template('member/qris_payment.html',
                           qr_data=qr_data,
                           topup_id=topup_request.id,
                           amount=amount)


@bp.route('/topup/qris/check/<int:topup_id>')
@login_required
def check_qris_payment(topup_id):
    """Check QRIS payment status via AJAX"""
    from qris_payment import QRISPaymentManager

    topup_request = TopUp.query.get_or_404(topup_id)

    # Verify ownership
    if topup_request.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Skip if already processed
    if topup_request.status != 'pending':
        return jsonify({
            'success': True,
            'status': topup_request.status,
            'redirect': url_for('main.dashboard')
        })

    qris_manager = QRISPaymentManager()
    verification = qris_manager.verify_payment(int(topup_request.amount))

    if verification['success']:
        # Payment found, update records
        payment_data = verification['payment_data']
        topup_request.status = 'completed'
        topup_request.reference = payment_data.get('issuer_reff', '')
        topup_request.completed_at = datetime.utcnow()

        # Add balance to user
        current_user.balance += topup_request.amount

        db.session.commit()

        # Send Telegram notification for successful top-up
        if telegram_notifier.enabled:
            try:
                asyncio.create_task(
                    telegram_notifier.send_topup_success_notification(
                        topup_request, current_user))
            except Exception as e:
                logging.error(
                    f"Failed to send top-up success notification: {str(e)}")

        return jsonify({
            'success': True,
            'status': 'completed',
            'message':
            f'Payment confirmed! Balance added: {format_currency(topup_request.amount)}',
            'redirect': url_for('main.dashboard')
        })
    else:
        return jsonify({
            'success': False,
            'status': 'pending',
            'message': 'Payment not yet received'
        })


@bp.route('/topup/qris/cancel/<int:topup_id>')
@login_required
def cancel_qris_payment(topup_id):
    """Cancel QRIS payment"""
    topup_request = TopUp.query.get_or_404(topup_id)

    # Verify ownership
    if topup_request.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('main.dashboard'))

    if topup_request.status == 'pending':
        topup_request.status = 'cancelled'
        db.session.commit()
        flash('QRIS payment cancelled', 'info')

    return redirect(url_for('main.topup'))


@bp.route('/packages/multiaddon')
@login_required
def multiaddon_packages():
    """Display Multi-Addon packages selection page"""
    if not current_user.xl_otp_verified:
        flash('❌ Verifikasi OTP XL diperlukan untuk membeli paket Multi-Addon!', 'error')
        return redirect(url_for('main.xl_otp_request'))
    
    from models import MultiAddonPackage
    packages = MultiAddonPackage.query.filter_by(is_active=True).all()
    
    return render_template('member/multiaddon_packages.html', packages=packages)

@bp.route('/packages/multiaddon/purchase', methods=['POST'])
@login_required
def purchase_multiaddon_packages():
    """Purchase selected multi-addon packages"""
    if not current_user.xl_otp_verified:
        flash('❌ Verifikasi OTP XL diperlukan untuk membeli paket!', 'error')
        return redirect(url_for('main.xl_otp_request'))

    try:
        from models import MultiAddonPackage, MultiAddonTransaction
        import json
        
        phone_number = request.form.get('phone_number')
        selected_package_ids = request.form.getlist('selected_packages')
        
        if not phone_number or not selected_package_ids:
            flash('❌ Data tidak lengkap. Silakan coba lagi.', 'error')
            return redirect(url_for('main.multiaddon_packages'))
        
        # Get selected packages
        packages = MultiAddonPackage.query.filter(
            MultiAddonPackage.id.in_(selected_package_ids),
            MultiAddonPackage.is_active == True
        ).all()
        
        if not packages:
            flash('❌ Paket tidak ditemukan.', 'error')
            return redirect(url_for('main.multiaddon_packages'))
        
        # Calculate total price
        total_price = sum(pkg.get_price_for_user(current_user) for pkg in packages)
        
        # Check user balance
        if current_user.balance < total_price:
            flash('❌ Saldo tidak mencukupi. Silakan top up terlebih dahulu.', 'error')
            return redirect(url_for('main.topup'))
        
        # Create transaction record
        transaction = MultiAddonTransaction(
            user_id=current_user.id,
            phone_number=phone_number,
            selected_packages=json.dumps([pkg.id for pkg in packages]),
            total_amount=total_price,
            total_packages=len(packages),
            status='processing'
        )
        db.session.add(transaction)
        db.session.flush()
        
        # Process packages
        xl_api = XLAPIManager()
        successful = 0
        failed = 0
        total_packages = len(packages)
        
        # Send initial progress notification
        if telegram_notifier.enabled:
            try:
                asyncio.create_task(
                    telegram_notifier.send_multiaddon_progress_notification(
                        transaction, current_user, f"📦 Memulai pembelian {total_packages} paket multi-addon...", 0, total_packages))
            except Exception as e:
                logging.error(f"Failed to send initial progress notification: {str(e)}")
        
        for i, package in enumerate(packages):
            current_progress = i + 1
            try:
                # Add delay between packages (except first)
                if i > 0:
                    import time
                    time.sleep(20)  # 20 second delay
                
                # Send progress notification
                if telegram_notifier.enabled:
                    try:
                        asyncio.create_task(
                            telegram_notifier.send_multiaddon_progress_notification(
                                transaction, current_user, f"📦 Memproses paket: {package.name}", current_progress, total_packages))
                    except Exception as e:
                        logging.error(f"Failed to send progress notification: {str(e)}")
                
                # Check if package needs retry logic (special codes)
                special_codes = ["PREMIUMXC", "SUPERXC", "STANDARDXC", "BASICXC", "YOUTUBEXC", "TIKTOK"]
                
                if package.package_code in special_codes:
                    # Retry until 422 response for special packages
                    max_attempts = 10
                    attempt = 0
                    package_success = False
                    
                    while not package_success and attempt < max_attempts:
                        attempt += 1
                        if attempt > 1:
                            import time
                            time.sleep(35)
                        
                        success, result = asyncio.run(xl_api.purchase_package(
                            current_user, phone_number, package.api_code, 'PULSA'))
                        
                        response_message = result.get('message', '') if isinstance(result, dict) else str(result)
                        
                        # Check for 422 success code
                        if "422" in response_message.lower():
                            package_success = True
                            successful += 1
                            
                            # Deduct balance for successful package
                            package_price = package.get_price_for_user(current_user)
                            current_user.balance -= package_price
                            current_user.counted += 1
                            
                            # Send success notification with progress
                            if telegram_notifier.enabled:
                                try:
                                    asyncio.create_task(
                                        telegram_notifier.send_multiaddon_success_notification(
                                            transaction, current_user, package, response_message, successful, total_packages))
                                except Exception as e:
                                    logging.error(f"Failed to send multiaddon success notification: {str(e)}")
                            break
                    
                    if not package_success:
                        failed += 1
                        # Send failed notification with progress
                        if telegram_notifier.enabled:
                            try:
                                asyncio.create_task(
                                    telegram_notifier.send_multiaddon_failed_notification(
                                        transaction, current_user, package, f"Gagal setelah {max_attempts} percobaan", failed, total_packages))
                            except Exception as e:
                                logging.error(f"Failed to send multiaddon failed notification: {str(e)}")
                
                else:
                    # Single attempt for non-special packages
                    success, result = asyncio.run(xl_api.purchase_package(
                        current_user, phone_number, package.api_code, 'PULSA'))
                    
                    response_message = result.get('message', '') if isinstance(result, dict) else str(result)
                    
                    if success or "422" in response_message.lower():
                        successful += 1
                        
                        # Deduct balance for successful package
                        package_price = package.get_price_for_user(current_user)
                        current_user.balance -= package_price
                        current_user.counted += 1
                        
                        # Send success notification with progress
                        if telegram_notifier.enabled:
                            try:
                                asyncio.create_task(
                                    telegram_notifier.send_multiaddon_success_notification(
                                        transaction, current_user, package, response_message, successful, total_packages))
                            except Exception as e:
                                logging.error(f"Failed to send multiaddon success notification: {str(e)}")
                    else:
                        failed += 1
                        # Send failed notification with progress
                        if telegram_notifier.enabled:
                            try:
                                asyncio.create_task(
                                    telegram_notifier.send_multiaddon_failed_notification(
                                        transaction, current_user, package, response_message, failed, total_packages))
                            except Exception as e:
                                logging.error(f"Failed to send multiaddon failed notification: {str(e)}")
            
            except Exception as e:
                logging.error(f"Error processing package {package.name}: {str(e)}")
                failed += 1
                # Send failed notification with progress
                if telegram_notifier.enabled:
                    try:
                        asyncio.create_task(
                            telegram_notifier.send_multiaddon_failed_notification(
                                transaction, current_user, package, str(e), failed, total_packages))
                    except Exception as e:
                        logging.error(f"Failed to send multiaddon failed notification: {str(e)}")
        
        # Update transaction
        transaction.successful_packages = successful
        transaction.failed_packages = failed
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send final summary notification
        if telegram_notifier.enabled:
            try:
                asyncio.create_task(
                    telegram_notifier.send_multiaddon_summary_notification(
                        transaction, current_user, successful, failed, total_packages))
            except Exception as e:
                logging.error(f"Failed to send multiaddon summary notification: {str(e)}")
        
        # Show result message
        if successful == len(packages):
            flash(f'✅ Semua {successful} paket berhasil diproses!', 'success')
        elif successful > 0:
            flash(f'⚠️ {successful} paket berhasil, {failed} paket gagal.', 'warning')
        else:
            flash(f'❌ Semua paket gagal diproses.', 'error')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Multi-addon purchase error: {str(e)}")
        flash('❌ Terjadi kesalahan saat memproses paket. Silakan coba lagi.', 'error')
        return redirect(url_for('main.multiaddon_packages'))

@bp.route('/quota-check')
@login_required
def quota_check():
    """Check XL quota for authenticated user"""
    if not current_user.xl_otp_verified or not current_user.xl_token:
        flash('❌ Verifikasi OTP XL diperlukan untuk mengecek kuota!', 'error')
        return redirect(url_for('main.xl_otp_request'))

    try:
        xl_api = XLAPIManager()
        success, result = asyncio.run(xl_api.check_quota(
            current_user.xl_token))

        if success:
            quotas = result
            return render_template('member/quota_check.html',
                                   quotas=quotas,
                                   phone=current_user.xl_phone)
        else:
            flash(f'❌ Gagal mengecek kuota: {result}', 'error')
            return redirect(url_for('main.packages'))

    except Exception as e:
        logging.error(f"Quota check error: {str(e)}")
        flash('❌ Terjadi kesalahan saat mengecek kuota.', 'error')
        return redirect(url_for('main.packages'))


# Template filters
@bp.app_template_filter('currency')
def currency_filter(value):
    return format_currency(value)


@bp.app_template_filter('phone')
def phone_filter(value):
    return format_phone(value)


@bp.app_template_filter('censor_phone')
def censor_phone_filter(value):
    """Censor phone number showing only last 4 digits"""
    if not value:
        return ""

    phone_str = str(value)
    if len(phone_str) <= 4:
        return phone_str

    # Show only last 4 digits, replace others with *
    censored = '*' * (len(phone_str) - 4) + phone_str[-4:]
    return censored


@bp.app_template_filter('datetime')
def datetime_filter(value):
    """Format timestamp to datetime"""
    from datetime import datetime

    if not value:
        return ""

    try:
        # Convert timestamp to datetime
        dt = datetime.fromtimestamp(float(value))
        return dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return str(value)


@bp.app_template_filter('datetime_wib')
def datetime_wib_filter(value):
    """Format datetime to WIB timezone"""
    from utils import format_datetime_wib
    return format_datetime_wib(value)
