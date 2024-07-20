from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

scheduler = BackgroundScheduler()

# Function to get weather
def get_weather(city):
    api_key = "a57cfb6e53msha7d93f2697beb61p158252jsncbcf2648195a"
    url = "https://weatherapi-com.p.rapidapi.com/current.json"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
    }
    querystring = {"q": city}

    response = requests.get(url, headers=headers, params=querystring)
    weather_data = response.json()
    return weather_data

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Define the login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    notices = Notice.query.all()
    weather_data = get_weather("Nasik")
    return render_template('index.html', notices=notices, weather_data=weather_data)

@app.route('/weather', methods=['POST'])
def weather():
    city = request.form['city']
    weather_data = get_weather(city)

    if 'error' in weather_data:
        error_message = weather_data['error']['message']
        return render_template('weather.html', error_message=error_message)
    else:
        return render_template('weather.html', weather_data=weather_data)


@app.route('/departments')
def department():
    return render_template('departments.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            session['logged_in'] = True
            return redirect(url_for('add_notice'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('admin_login.html')

@app.route('/admin/add_notice', methods=['GET', 'POST'])
@login_required
def add_notice():
    notices = Notice.query.all()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        notice = Notice(title=title, content=content)
        db.session.add(notice)
        db.session.commit()
        flash('Notice added successfully', 'success')
        return redirect(url_for('index'))
    return render_template('add_notice.html',  notices=notices)

from flask import jsonify

@app.route('/notices')
def get_notices():
    notices = Notice.query.all()
    notices_data = [{'id': notice.id, 'title': notice.title, 'content': notice.content} for notice in notices]
    return jsonify(notices_data)

from flask import jsonify, request

@app.route('/admin/edit_notice/<int:id>', methods=['POST'])
@login_required
def edit_notice(id):
    notice = Notice.query.get(id)
    if notice:
        data = request.json
        notice.title = data['title']
        notice.content = data['content']
        db.session.commit()
        return jsonify({'message': 'Notice updated successfully'}), 200
    
    else:
        return jsonify({'error': 'Notice not found'}), 404


from flask import jsonify

@app.route('/admin/delete_notice/<int:id>', methods=['POST'])
@login_required
def delete_notice(id):
    notice = Notice.query.get(id)
    if notice:
        db.session.delete(notice)
        db.session.commit()
        return jsonify({'message': 'Notice deleted successfully'}), 200
    else:
        return jsonify({'error': 'Notice not found'}), 404

# Function to periodically update weather data
def update_weather():
    city = "Nasik"  # You can change this to a variable if needed
    weather_data = get_weather(city)
    # You can store the weather data in the database or any other desired action
    print("Weather updated successfully")

# Schedule the weather update task to run every hour
scheduler.add_job(update_weather, trigger=IntervalTrigger(minutes= 60))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        scheduler.start()
    app.run(debug=True)

