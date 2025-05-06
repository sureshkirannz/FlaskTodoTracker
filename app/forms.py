from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    organization_name = StringField('Organization Name', validators=[DataRequired(), Length(min=2, max=100)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already in use. Please use a different email address.')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class OrganizationSettingsForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    primary_color = StringField('Primary Color', validators=[Optional(), Length(max=20)])
    secondary_color = StringField('Secondary Color', validators=[Optional(), Length(max=20)])
    logo = FileField('Logo', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Settings')

class StaffForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=64)])
    position = StringField('Position', validators=[Optional(), Length(max=64)])
    photo = FileField('Photo', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Staff')

class VisitorCheckInForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    purpose = StringField('Purpose of Visit', validators=[DataRequired(), Length(max=200)])
    staff_id = SelectField('Who are you visiting?', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Check In')

class VisitorCheckOutForm(FlaskForm):
    visitor_id = SelectField('Select Your Name', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Check Out')

class PreregisterVisitorForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    purpose = StringField('Purpose of Visit', validators=[DataRequired(), Length(max=200)])
    expected_arrival = StringField('Expected Arrival (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    staff_id = SelectField('Host', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Preregister Visitor')

class EmailTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(min=2, max=100)])
    subject = StringField('Email Subject', validators=[DataRequired(), Length(min=2, max=200)])
    body = TextAreaField('Email Body', validators=[DataRequired()])
    template_type = SelectField('Template Type', choices=[
        ('check_in', 'Check-in Notification'),
        ('check_out', 'Check-out Notification'),
        ('preregister', 'Preregistration Confirmation')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Template')

class DocumentForm(FlaskForm):
    name = StringField('Document Name', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Document Content', validators=[DataRequired()])
    document_type = SelectField('Document Type', choices=[
        ('nda', 'Non-Disclosure Agreement'),
        ('policy', 'Company Policy'),
        ('waiver', 'Liability Waiver')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Document')

class BadgeTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(min=2, max=100)])
    template_data = TextAreaField('Template JSON', validators=[DataRequired()])
    submit = SubmitField('Save Badge Template')

class ReportFilterForm(FlaskForm):
    start_date = StringField('Start Date (YYYY-MM-DD)', validators=[Optional()])
    end_date = StringField('End Date (YYYY-MM-DD)', validators=[Optional()])
    staff_id = SelectField('Host', coerce=int, validators=[Optional()])
    purpose = StringField('Purpose', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Filter Reports')
    
class SubscriptionPlanForm(FlaskForm):
    plan_id = SelectField('Subscription Plan', validators=[DataRequired()], 
                         choices=[
                             ('free', 'Free'),
                             ('basic', 'Basic'),
                             ('professional', 'Professional'),
                             ('enterprise', 'Enterprise')
                         ])
    billing_cycle = SelectField('Billing Cycle', validators=[DataRequired()],
                              choices=[
                                  ('monthly', 'Monthly'),
                                  ('yearly', 'Yearly (Save up to 17%)')
                              ])
    submit = SubmitField('Continue to Payment')