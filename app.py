from flask import Flask, render_template, request, jsonify, session, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json
import os
import secrets
import bleach
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Security middleware
Talisman(app, force_https=False)  # Set to True in production
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Input sanitization
def sanitize_input(data):
    if isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        return bleach.clean(data, tags=[], strip=True)
    return data

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# User management functions
def get_current_user():
    if 'user_id' not in session:
        return None
    users = load_data('users')
    return users.get(session['user_id'])

def get_user_data(filename, user_id=None):
    if not user_id:
        user = get_current_user()
        if not user:
            return {}
        user_id = user['id']
    
    data = load_data(filename)
    return data.get(user_id, {})

def save_user_data(filename, data, user_id=None):
    if not user_id:
        user = get_current_user()
        if not user:
            return
        user_id = user['id']
    
    all_data = load_data(filename)
    all_data[user_id] = data
    save_data(filename, all_data)

# Data storage (simple JSON files)
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename):
    path = os.path.join(DATA_DIR, f'{filename}.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    # Validate filename to prevent path traversal
    if not filename.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Invalid filename")
    
    path = os.path.join(DATA_DIR, f'{filename}.json')
    # Ensure path is within DATA_DIR
    if not os.path.abspath(path).startswith(os.path.abspath(DATA_DIR)):
        raise ValueError("Path traversal attempt detected")
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    if 'user_id' in session:
        user = get_current_user()
        if user['role'] == 'parent':
            return redirect('/parent')
        else:
            return redirect('/athlete/dashboard')
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        data = sanitize_input(request.json)
        
        # Validate parent registration
        if not all(k in data for k in ['parent_name', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if email already exists
        users = load_data('users')
        for user in users.values():
            if user.get('email', '').lower() == data['email'].lower():
                return jsonify({'error': 'Email already registered'}), 400
        
        # Create parent account only
        parent_id = str(uuid.uuid4())
        family_id = str(uuid.uuid4())
        
        users[parent_id] = {
            'id': parent_id,
            'name': data['parent_name'],
            'email': data['email'],
            'role': 'parent',
            'family_id': family_id,
            'children': [],  # Will store child IDs
            'password_hash': generate_password_hash(data['password']),
            'created_at': datetime.now().isoformat()
        }
        
        save_data('users', users)
        
        # Auto-login parent
        session['user_id'] = parent_id
        return jsonify({'status': 'success', 'redirect': '/parent/setup'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        data = sanitize_input(request.json)
        
        if not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Missing credentials'}), 400
        
        users = load_data('users')
        user = None
        
        # Find user by email (parents only)
        for u in users.values():
            if u.get('email', '').lower() == data['email'].lower() and u['role'] == 'parent':
                user = u
                break
        
        if not user or not check_password_hash(user['password_hash'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = user['id']
        return jsonify({'status': 'success', 'redirect': '/parent'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/parent/setup')
@require_auth
def parent_setup():
    user = get_current_user()
    if user['role'] != 'parent':
        return redirect('/')
    return render_template('parent_setup.html', user=user)

@app.route('/parent')
@require_auth
def parent_dashboard():
    user = get_current_user()
    if user['role'] != 'parent':
        return redirect('/')
    
    # Get children data
    users = load_data('users')
    children = [users[child_id] for child_id in user.get('children', []) if child_id in users]
    
    return render_template('parent_dashboard.html', user=user, children=children)

@app.route('/api/add-child', methods=['POST'])
@limiter.limit("5 per minute")
@require_auth
def add_child():
    user = get_current_user()
    if user['role'] != 'parent':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = sanitize_input(request.json)
    if not all(k in data for k in ['name', 'age', 'sport']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create child profile
    child_id = str(uuid.uuid4())
    pin = str(uuid.uuid4())[:6].upper()  # Simple 6-char PIN for child
    
    users = load_data('users')
    users[child_id] = {
        'id': child_id,
        'name': data['name'],
        'age': int(data['age']),
        'sport': data['sport'],
        'role': 'child',
        'parent_id': user['id'],
        'family_id': user['family_id'],
        'pin': pin,  # Simple PIN instead of password
        'created_at': datetime.now().isoformat(),
        'permissions': {
            'can_checkin': True,
            'can_view_stats': True,
            'can_post_social': False  # Parent controls social features
        }
    }
    
    # Add child to parent's children list
    user['children'] = user.get('children', [])
    user['children'].append(child_id)
    users[user['id']] = user
    
    save_data('users', users)
    
    return jsonify({
        'status': 'success', 
        'child_id': child_id,
        'pin': pin,
        'message': f'Child profile created. PIN: {pin}'
    })

@app.route('/athlete')
@require_auth
def athlete_app():
    user = get_current_user()
    return render_template('athlete_app.html', user=user)

@app.route('/parent/athlete-view')
def parent_athlete_view():
    return render_template('athlete_app.html')  # Parent can access athlete interface

@app.route('/parent/enhanced')
def enhanced_dashboard():
    return render_template('enhanced_dashboard.html')

@app.route('/child/dashboard')
@require_auth
def child_dashboard():
    user = get_current_user()
    if user['role'] != 'child':
        return redirect('/')
    return render_template('child_dashboard.html', user=user)

@app.route('/child/checkin')
@require_auth
def child_checkin():
    user = get_current_user()
    if user['role'] != 'child' or not user.get('permissions', {}).get('can_checkin'):
        return redirect('/child/dashboard')
    return render_template('child_checkin.html', user=user)

@app.route('/child-login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def child_login():
    if request.method == 'POST':
        data = sanitize_input(request.json)
        
        if not all(k in data for k in ['name', 'pin']):
            return jsonify({'error': 'Missing credentials'}), 400
        
        users = load_data('users')
        child = None
        
        # Find child by name and PIN
        for u in users.values():
            if (u.get('role') == 'child' and 
                u['name'].lower() == data['name'].lower() and 
                u.get('pin') == data['pin'].upper()):
                child = u
                break
        
        if not child:
            return jsonify({'error': 'Invalid name or PIN'}), 401
        
        session['user_id'] = child['id']
        return jsonify({'status': 'success', 'redirect': '/child/dashboard'})
    
    return render_template('child_login.html')

@app.route('/phase2')
def phase2_features():
    return render_template('phase2_dashboard.html')

@app.route('/coach-communication')
def coach_communication():
    return render_template('coach_communication.html')

@app.route('/activity-import')
def activity_import_page():
    return render_template('activity_import.html')

@app.route('/advanced-analytics')
def advanced_analytics_page():
    return render_template('advanced_analytics.html')

@app.route('/mobile')
def mobile_app():
    return render_template('mobile_app.html')

@app.route('/api/activity-import', methods=['POST'])
@limiter.limit("10 per minute")
@require_auth
def import_activity_data():
    if not request.json:
        return jsonify({'error': 'Invalid data'}), 400
    
    user = get_current_user()
    data = sanitize_input(request.json)
    
    # Validate activity data
    required_fields = ['steps', 'active_minutes', 'calories']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    today = str(date.today())
    activity_data = {
        'steps': int(data['steps']),
        'active_minutes': int(data['active_minutes']),
        'calories': int(data['calories']),
        'distance': float(data.get('distance', 0)),
        'heart_rate_avg': int(data.get('heart_rate_avg', 0)),
        'imported_at': datetime.now().isoformat(),
        'source': data.get('source', 'phone_app')
    }
    
    user_activity = get_user_data('activity_imports')
    user_activity[today] = activity_data
    save_user_data('activity_imports', user_activity)
    
    return jsonify({'status': 'imported', 'date': today})

@app.route('/api/checkin', methods=['POST'])
@limiter.limit("10 per minute")
@require_auth
def daily_checkin():
    if not request.json:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    user = get_current_user()
    data = sanitize_input(request.json)
    
    # Validate required fields and ranges
    if not isinstance(data.get('sleep_hours'), (int, float)) or not (0 <= data.get('sleep_hours', 0) <= 24):
        return jsonify({'error': 'Invalid sleep hours'}), 400
    if not isinstance(data.get('mood'), int) or not (1 <= data.get('mood', 0) <= 5):
        return jsonify({'error': 'Invalid mood value'}), 400
    if not isinstance(data.get('water_bottles'), int) or not (0 <= data.get('water_bottles', 0) <= 20):
        return jsonify({'error': 'Invalid water bottles'}), 400
    
    today = str(date.today())
    data['user_id'] = user['id']
    data['athlete_name'] = user['name']
    data['timestamp'] = datetime.now().isoformat()
    
    # Get user's checkin data
    user_checkins = get_user_data('checkins')
    user_checkins[today] = data
    save_user_data('checkins', user_checkins)
    
    insights = generate_daily_insights(data)
    
    return jsonify({'status': 'success', 'insights': insights})

def generate_daily_insights(data):
    insights = []
    
    # Sleep optimization
    sleep_hours = data.get('sleep_hours', 0)
    if sleep_hours < 8:
        insights.append(f'Sleep deficit: {8 - sleep_hours:.1f}h. Early bedtime recommended.')
    elif sleep_hours > 10:
        insights.append('Excellent sleep! Recovery optimized.')
    
    # Hydration intelligence
    water_bottles = data.get('water_bottles', 0)
    if water_bottles < 6:
        insights.append(f'Hydration alert: {8 - water_bottles} more bottles needed today')
    
    # Performance correlation
    mood = data.get('mood', 0)
    training = data.get('training_completed', False)
    
    if mood <= 2 and training:
        insights.append('Low mood + training = burnout risk. Consider active recovery.')
    elif mood >= 4 and training:
        insights.append('Great mindset + training = peak performance zone!')
    
    # Nutrition timing
    protein = data.get('protein_level', 'low')
    if training and protein == 'low':
        insights.append('Post-training protein window: consume within 30 minutes')
    
    return insights

@app.route('/api/data/<date_str>')
def get_data(date_str):
    checkins = load_data('checkins')
    return jsonify(checkins.get(date_str, {}))

@app.route('/api/schedule')
def smart_schedule():
    from datetime import datetime, timedelta
    import calendar
    
    today = datetime.now()
    checkins = load_data('checkins')
    recent_data = list(checkins.values())[-3:]  # Last 3 days
    
    suggestions = []
    
    # Adaptive scheduling based on recent performance
    avg_sleep = sum(d.get('sleep_hours', 8) for d in recent_data) / max(len(recent_data), 1)
    avg_mood = sum(d.get('mood', 3) for d in recent_data) / max(len(recent_data), 1)
    
    if today.hour < 12:
        if avg_sleep < 7.5:
            suggestions.append({'time': '4:00 PM', 'activity': '😴 Light Recovery Session', 'priority': 'high', 'reason': 'Low sleep detected'})
        else:
            suggestions.append({'time': '4:30 PM', 'activity': '⚽ Training Session', 'priority': 'high'})
        
        if calendar.weekday(today.year, today.month, today.day) in [5, 6]:  # Weekend
            suggestions.append({'time': '10:00 AM', 'activity': '🏃 Extra Skills Practice', 'priority': 'medium'})
    else:
        if avg_mood < 3:
            suggestions.append({'time': '8:00 PM', 'activity': '🧘 Extended Mental Balance', 'priority': 'high', 'reason': 'Mood support needed'})
        else:
            suggestions.append({'time': '8:30 PM', 'activity': '🧘 Mental Balance', 'priority': 'medium'})
    
    return jsonify({'suggestions': suggestions})

@app.route('/api/injury-risk')
def injury_risk_assessment():
    checkins = load_data('checkins')
    recent_data = list(checkins.values())[-7:]  # Last 7 days
    
    if len(recent_data) < 3:
        return jsonify({'risk_level': 'unknown', 'score': 0})
    
    # Risk factors
    sleep_risk = sum(1 for d in recent_data if d.get('sleep_hours', 8) < 7) / len(recent_data)
    training_load = sum(1 for d in recent_data if d.get('training_completed')) / len(recent_data)
    mood_risk = sum(1 for d in recent_data if d.get('mood', 3) < 3) / len(recent_data)
    
    # Calculate risk score (0-100)
    risk_score = (sleep_risk * 40) + (training_load * 30) + (mood_risk * 30)
    
    if risk_score > 60: risk_level = 'high'
    elif risk_score > 30: risk_level = 'moderate'
    else: risk_level = 'low'
    
    return jsonify({
        'risk_level': risk_level,
        'score': round(risk_score, 1),
        'factors': {
            'sleep_issues': round(sleep_risk * 100, 1),
            'training_load': round(training_load * 100, 1),
            'mood_concerns': round(mood_risk * 100, 1)
        }
    })

@app.route('/api/nutrition-ai')
def nutrition_recommendations():
    checkins = load_data('checkins')
    today_data = checkins.get(str(date.today()), {})
    
    recommendations = []
    
    # Hydration check
    water_intake = today_data.get('water_bottles', 0)
    if water_intake < 6:
        recommendations.append({
            'type': 'hydration',
            'message': f'Drink {8 - water_intake} more bottles today',
            'priority': 'high'
        })
    
    # Protein timing
    protein_level = today_data.get('protein_level', 'low')
    training_today = today_data.get('training_completed', False)
    
    if training_today and protein_level == 'low':
        recommendations.append({
            'type': 'protein',
            'message': 'Post-workout protein needed - try chocolate milk or protein shake',
            'priority': 'high'
        })
    
    # Pre-sleep nutrition
    from datetime import datetime
    if datetime.now().hour >= 20:
        recommendations.append({
            'type': 'recovery',
            'message': 'Consider light snack with protein for overnight recovery',
            'priority': 'medium'
        })
    
    return jsonify({'recommendations': recommendations})

@app.route('/api/goals', methods=['GET', 'POST'])
def goals_management():
    goals_data = load_data('goals')
    
    if request.method == 'POST':
        goal = request.json
        goal['id'] = len(goals_data) + 1
        goal['created_date'] = str(date.today())
        goal['status'] = 'active'
        goals_data[str(goal['id'])] = goal
        save_data('goals', goals_data)
        return jsonify({'status': 'success', 'goal_id': goal['id']})
    
    return jsonify({'goals': list(goals_data.values())})

@app.route('/api/growth-tracking', methods=['GET', 'POST'])
def growth_tracking():
    growth_data = load_data('growth')
    
    if request.method == 'POST':
        data = request.json
        today = str(date.today())
        growth_data[today] = data
        save_data('growth', growth_data)
        return jsonify({'status': 'success'})
    
    # Calculate growth trends
    recent_entries = list(growth_data.items())[-12:]  # Last 12 entries
    if len(recent_entries) >= 2:
        latest = recent_entries[-1][1]
        previous = recent_entries[0][1]
        
        height_change = latest.get('height', 0) - previous.get('height', 0)
        weight_change = latest.get('weight', 0) - previous.get('weight', 0)
        
        trends = {
            'height_change': height_change,
            'weight_change': weight_change,
            'latest_height': latest.get('height', 0),
            'latest_weight': latest.get('weight', 0)
        }
    else:
        trends = {'height_change': 0, 'weight_change': 0, 'latest_height': 0, 'latest_weight': 0}
    
    return jsonify({'trends': trends, 'history': growth_data})

@app.route('/api/wearable-sync', methods=['POST'])
def wearable_sync():
    # Simulate wearable data integration
    wearable_data = request.json
    today = str(date.today())
    
    # Store wearable data
    wearables = load_data('wearables')
    wearables[today] = {
        'heart_rate_avg': wearable_data.get('heart_rate_avg', 0),
        'steps': wearable_data.get('steps', 0),
        'sleep_quality': wearable_data.get('sleep_quality', 0),
        'recovery_score': wearable_data.get('recovery_score', 0)
    }
    save_data('wearables', wearables)
    
    return jsonify({'status': 'synced', 'data_points': len(wearable_data)})

@app.route('/api/activity-stats')
@require_auth
def get_activity_stats():
    user_activity = get_user_data('activity_imports')
    recent_data = list(user_activity.values())[-7:]  # Last 7 days
    
    if not recent_data:
        return jsonify({'status': 'no_data'})
    
    avg_steps = sum(d.get('steps', 0) for d in recent_data) / len(recent_data)
    avg_active_minutes = sum(d.get('active_minutes', 0) for d in recent_data) / len(recent_data)
    avg_calories = sum(d.get('calories', 0) for d in recent_data) / len(recent_data)
    
    return jsonify({
        'avg_steps': round(avg_steps),
        'avg_active_minutes': round(avg_active_minutes),
        'avg_calories': round(avg_calories),
        'days_tracked': len(recent_data),
        'step_goal_met': sum(1 for d in recent_data if d.get('steps', 0) >= 10000),
        'activity_goal_met': sum(1 for d in recent_data if d.get('active_minutes', 0) >= 60)
    })





@app.route('/api/competition-calendar', methods=['GET', 'POST'])
def competition_calendar():
    calendar_data = load_data('competitions')
    
    if request.method == 'POST':
        event = request.json
        event['id'] = len(calendar_data) + 1
        calendar_data[str(event['id'])] = event
        save_data('competitions', calendar_data)
        return jsonify({'status': 'success'})
    
    # Get upcoming events
    from datetime import datetime, timedelta
    today = datetime.now().date()
    upcoming = []
    
    for event in calendar_data.values():
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        if event_date >= today:
            days_until = (event_date - today).days
            event['days_until'] = days_until
            upcoming.append(event)
    
    upcoming.sort(key=lambda x: x['days_until'])
    
    return jsonify({'upcoming_events': upcoming[:5]})

@app.route('/api/sleep-analysis')
def sleep_analysis():
    checkins = load_data('checkins')
    recent_data = list(checkins.values())[-30:]  # Last 30 days
    
    if not recent_data:
        return jsonify({'status': 'no_data'})
    
    sleep_data = [d.get('sleep_hours', 0) for d in recent_data]
    mood_data = [d.get('mood', 0) for d in recent_data]
    
    # Sleep quality analysis
    avg_sleep = sum(sleep_data) / len(sleep_data)
    sleep_consistency = 1 - (max(sleep_data) - min(sleep_data)) / 12  # 0-1 scale
    
    # Sleep-mood correlation
    good_sleep_days = [i for i, s in enumerate(sleep_data) if s >= 8]
    avg_mood_good_sleep = sum(mood_data[i] for i in good_sleep_days) / max(len(good_sleep_days), 1)
    
    return jsonify({
        'average_sleep': round(avg_sleep, 1),
        'consistency_score': round(sleep_consistency * 100, 1),
        'optimal_sleep_days': len([s for s in sleep_data if s >= 8]),
        'mood_correlation': round(avg_mood_good_sleep, 1),
        'recommendations': [
            'Target 9 hours nightly' if avg_sleep < 8.5 else 'Excellent sleep duration',
            'Improve consistency' if sleep_consistency < 0.8 else 'Great sleep routine'
        ]
    })

@app.route('/api/performance-trends')
def performance_trends():
    checkins = load_data('checkins')
    recent_data = list(checkins.values())[-14:]  # Last 2 weeks
    
    if len(recent_data) < 7:
        return jsonify({'status': 'insufficient_data'})
    
    # Split into two weeks
    week1 = recent_data[:7]
    week2 = recent_data[7:]
    
    def week_stats(data):
        return {
            'avg_sleep': sum(d.get('sleep_hours', 0) for d in data) / len(data),
            'avg_mood': sum(d.get('mood', 0) for d in data) / len(data),
            'training_rate': sum(1 for d in data if d.get('training_completed')) / len(data) * 100,
            'hydration': sum(d.get('water_bottles', 0) for d in data) / len(data)
        }
    
    w1_stats = week_stats(week1)
    w2_stats = week_stats(week2)
    
    trends = {
        'sleep_trend': 'improving' if w2_stats['avg_sleep'] > w1_stats['avg_sleep'] else 'declining',
        'mood_trend': 'improving' if w2_stats['avg_mood'] > w1_stats['avg_mood'] else 'declining',
        'training_trend': 'improving' if w2_stats['training_rate'] > w1_stats['training_rate'] else 'declining',
        'hydration_trend': 'improving' if w2_stats['hydration'] > w1_stats['hydration'] else 'declining'
    }
    
    return jsonify({
        'week1': w1_stats,
        'week2': w2_stats,
        'trends': trends,
        'overall_direction': 'positive' if sum(1 for t in trends.values() if t == 'improving') >= 3 else 'needs_attention'
    })

@app.route('/api/team-social', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
@require_auth
def team_social():
    user = get_current_user()
    family_social = get_user_data('team_social')
    
    if request.method == 'POST':
        if not request.json or 'content' not in request.json:
            return jsonify({'error': 'Invalid post data'}), 400
        
        content = sanitize_input(request.json.get('content', ''))
        if len(content) > 500:
            return jsonify({'error': 'Post too long'}), 400
        if len(content.strip()) == 0:
            return jsonify({'error': 'Empty post'}), 400
        
        post = {
            'id': str(uuid.uuid4()),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'author': user['name'],
            'likes': 0
        }
        
        family_social[post['id']] = post
        save_user_data('team_social', family_social)
        return jsonify({'status': 'posted', 'post_id': post['id']})
    
    recent_posts = list(family_social.values())[-10:]
    return jsonify({'posts': recent_posts})

@app.route('/api/recovery-optimizer')
@require_auth
def recovery_optimizer():
    user_checkins = get_user_data('checkins')
    recent_data = list(user_checkins.values())[-7:]  # Last week
    
    if not recent_data:
        return jsonify({'status': 'no_data'})
    
    # Calculate recovery metrics
    avg_sleep = sum(d.get('sleep_hours', 0) for d in recent_data) / len(recent_data)
    avg_mood = sum(d.get('mood', 0) for d in recent_data) / len(recent_data)
    training_load = sum(1 for d in recent_data if d.get('training_completed'))
    
    # Recovery recommendations
    recommendations = []
    if avg_sleep < 8:
        recommendations.append({'type': 'sleep', 'priority': 'high', 'action': 'Increase sleep by 30-60 minutes'})
    if avg_mood < 3.5:
        recommendations.append({'type': 'mental', 'priority': 'medium', 'action': 'Add meditation or relaxation time'})
    if training_load > 5:
        recommendations.append({'type': 'training', 'priority': 'high', 'action': 'Schedule active recovery day'})
    
    recovery_score = min(100, (avg_sleep/9 * 40) + (avg_mood/5 * 35) + ((7-training_load)/7 * 25))
    
    return jsonify({
        'recovery_score': round(recovery_score, 1),
        'sleep_quality': round(avg_sleep, 1),
        'mental_state': round(avg_mood, 1),
        'training_load': training_load,
        'recommendations': recommendations,
        'next_action': recommendations[0]['action'] if recommendations else 'Maintain current routine'
    })

@app.route('/api/analytics')
@require_auth
def get_analytics():
    user_checkins = get_user_data('checkins')
    recent_data = list(user_checkins.values())[-7:]  # Last 7 days
    
    if not recent_data:
        return jsonify({'predictability_index': 0, 'status': 'No data'})
    
    # Core metrics
    avg_sleep = sum(d.get('sleep_hours', 0) for d in recent_data) / len(recent_data)
    avg_mood = sum(d.get('mood', 0) for d in recent_data) / len(recent_data)
    training_consistency = sum(1 for d in recent_data if d.get('training_completed')) / len(recent_data) * 100
    homework_completion = sum(1 for d in recent_data if d.get('homework_done')) / len(recent_data) * 100
    avg_hydration = sum(d.get('water_bottles', 0) for d in recent_data) / len(recent_data)
    
    # Predictability Index (0-100)
    sleep_score = min(100, (avg_sleep / 9.0) * 100)  # Target: 9 hours
    nutrition_score = min(100, (avg_hydration / 8.0) * 100)  # Target: 8 bottles
    recovery_score = min(100, (avg_mood / 5.0) * 100)  # Target: 5/5 mood
    training_score = training_consistency
    mental_score = min(100, (avg_mood / 5.0) * 100)
    
    predictability_index = (
        sleep_score * 0.25 +
        nutrition_score * 0.25 +
        recovery_score * 0.20 +
        training_score * 0.15 +
        mental_score * 0.15
    )
    
    # Status color coding
    if predictability_index >= 80: status = '🟢 Optimal'
    elif predictability_index >= 60: status = '🟡 Moderate'
    else: status = '🔴 Overload'
    
    # AI Alerts
    alerts = []
    if avg_sleep < 8: alerts.append('⚠️ Sleep below target - injury risk increased')
    if avg_hydration < 6: alerts.append('💧 Hydration low - performance may suffer')
    if training_consistency > 85 and avg_sleep < 8: alerts.append('🚨 High training + low sleep = overload risk')
    if avg_mood < 3: alerts.append('😟 Mood trending low - consider rest day')
    
    return jsonify({
        'predictability_index': round(predictability_index, 1),
        'status': status,
        'avg_sleep': avg_sleep,
        'avg_mood': avg_mood,
        'training_consistency': training_consistency,
        'homework_completion': homework_completion,
        'avg_hydration': avg_hydration,
        'alerts': alerts,
        'scores': {
            'sleep': round(sleep_score, 1),
            'nutrition': round(nutrition_score, 1),
            'recovery': round(recovery_score, 1),
            'training': round(training_score, 1),
            'mental': round(mental_score, 1)
        }
    })

# Initialize empty data structure
def init_data_structure():
    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Initialize empty data files if they don't exist
    data_files = ['users', 'checkins', 'goals', 'competitions', 'team_social', 'growth', 'wearables', 'activity_imports']
    for filename in data_files:
        if not os.path.exists(os.path.join(DATA_DIR, f'{filename}.json')):
            save_data(filename, {})

if __name__ == '__main__':
    init_data_structure()
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)