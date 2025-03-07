from flask import Blueprint, render_template, url_for, flash, redirect, request
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from app.forms import RegistrationForm, LoginForm
from app import bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('chat.chatroom'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        User.create(username=form.username.data, email=form.email.data, password_hash=hashed_pw)
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.signin'))
    return render_template('signup.html', title='Sign Up', form=form)

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('chat.chatroom'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat.chatroom'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html', title='Sign In', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.signin'))