from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, BooleanField, TextAreaField, HiddenField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError, Optional
from models import User, UserRole

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class PackageForm(FlaskForm):
    name = StringField('Package Name', validators=[DataRequired()])
    code = StringField('Package Code', validators=[DataRequired()])
    price_member = FloatField('Member Price', validators=[DataRequired(), NumberRange(min=0)])
    price_reseller = FloatField('Reseller Price', validators=[DataRequired(), NumberRange(min=0)])
    api_code = StringField('API Code', validators=[DataRequired()])
    package_ewallet = StringField('Package E-Wallet Code')
    payment_methods = SelectMultipleField('Payment Methods', 
                                        choices=[('PULSA', 'PULSA'), ('DANA', 'DANA'), ('QRIS', 'QRIS')],
                                        validators=[DataRequired()])
    is_active = BooleanField('Is Active', default=True)
    submit = SubmitField('Save Package')

class PurchaseForm(FlaskForm):
    package_id = HiddenField('Package ID', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    payment_method = SelectField('Payment Method', choices=[('PULSA', 'PULSA'), ('DANA', 'DANA'), ('QRIS', 'QRIS')], validators=[DataRequired()])

class TopUpForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=10000, max=10000000, message="Minimum Rp 10.000, Maximum Rp 10.000.000")])
    payment_method = SelectField('Payment Method', choices=[('qris', 'QRIS'), ('bank', 'Bank Transfer')], validators=[DataRequired()])

    def validate_amount(self, amount):
        # Additional validation for QRIS payment
        if self.payment_method.data == 'qris':
            if amount.data < 10000:
                raise ValidationError('Minimum top-up amount for QRIS is Rp 10.000')
            if amount.data > 10000000:
                raise ValidationError('Maximum top-up amount for QRIS is Rp 10.000.000')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    role = SelectField('Role', choices=[(role.value, role.value.title()) for role in UserRole], validators=[DataRequired()])
    balance = FloatField('Balance', validators=[NumberRange(min=0)])
    is_active = BooleanField('Active')

class BalanceAdjustForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    action = SelectField('Action', choices=[('add', 'Add Balance'), ('subtract', 'Subtract Balance')], validators=[DataRequired()])
    note = TextAreaField('Note')

class XLLoginForm(FlaskForm):
    phone_number = StringField('XL Phone Number', validators=[DataRequired(), Length(min=10, max=15)])

class XLOTPRequestForm(FlaskForm):
    xl_phone_number = StringField('Nomor XL', validators=[
        DataRequired(message="Nomor XL harus diisi"),
        Length(min=10, max=15, message="Nomor XL tidak valid")
    ], render_kw={'placeholder': '628xxxxxxxxx'})

class XLOTPVerifyForm(FlaskForm):
    otp_code = StringField('Kode OTP', validators=[
        DataRequired(message="Kode OTP harus diisi"),
        Length(min=4, max=8, message="Kode OTP tidak valid")
    ], render_kw={'placeholder': 'Masukkan kode OTP'})

class PaymentMethodSettingsForm(FlaskForm):
    pulsa_enabled = BooleanField('Aktifkan PULSA')
    dana_enabled = BooleanField('Aktifkan DANA')
    qris_enabled = BooleanField('Aktifkan QRIS')
    submit = SubmitField('Simpan Pengaturan')

class WebsiteSettingsForm(FlaskForm):
    site_title = StringField('Site Title', validators=[DataRequired(), Length(min=1, max=100)])
    site_description = TextAreaField('Site Description', validators=[Length(max=500)], render_kw={"rows": 3})
    logo_url = StringField('Logo URL', validators=[Length(max=500)])
    favicon_url = StringField('Favicon URL', validators=[Length(max=500)])
    submit = SubmitField('Save Settings')

class TelegramSettingsForm(FlaskForm):
    bot_token = StringField('Bot Token', validators=[DataRequired()])
    group_id = StringField('Group ID', validators=[DataRequired()])
    website_name = StringField('Website Name')
    website_url = StringField('Website URL')
    success_message_format = TextAreaField('Success Message Format', render_kw={"rows": 12})
    failed_message_format = TextAreaField('Failed Message Format', render_kw={"rows": 12})
    topup_pending_message_format = TextAreaField('Top-Up Pending Message Format', render_kw={"rows": 10})
    topup_success_message_format = TextAreaField('Top-Up Success Message Format', render_kw={"rows": 10})
    topup_failed_message_format = TextAreaField('Top-up Failed Message Format', 
                                               render_kw={'rows': 10})

    # XUT-specific notification formats
    xut_success_message_format = TextAreaField('XUT Success Message Format', 
                                              render_kw={'rows': 10})
    xut_failed_message_format = TextAreaField('XUT Failed Message Format', 
                                             render_kw={'rows': 10})

    is_enabled = BooleanField('Enable Telegram Notifications')
    submit = SubmitField('Save Settings')