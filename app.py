from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os

app = Flask(__name__)
app.secret_key = "tarikur_core_2026"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'club.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Admin Key ---
ADMIN_PASSWORD = "admin123"

# --- Models ---
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    attendances = db.relationship('Attendance', backref='member', cascade="all, delete-orphan", lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    time = db.Column(db.String(100))
    description = db.Column(db.Text)
    attendances = db.relationship('Attendance', backref='event', cascade="all, delete-orphan", lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

# --- Auth ---
@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# --- Routes ---
@app.route('/')
def index():
    is_admin = session.get('admin', False)
    members = Member.query.order_by(Member.id.asc()).all()
    events = Event.query.order_by(Event.id.desc()).all()
    total_m = len(members)
    total_a = Attendance.query.count()
    
    # Best Analytics Leaderboard
    top_members = db.session.query(Member.name, Member.role, func.count(Attendance.id).label('total'))\
        .join(Attendance).group_by(Member.id).order_by(func.count(Attendance.id).desc()).limit(5).all()
        
    return render_template('index.html', members=members, events=events, total_m=total_m, total_a=total_a, top_members=top_members, is_admin=is_admin)

@app.route('/add_member', methods=['POST'])
def add_member():
    if session.get('admin'):
        db.session.add(Member(name=request.form.get('name'), role=request.form.get('role')))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_member/<int:id>', methods=['POST'])
def edit_member(id):
    if session.get('admin'):
        m = Member.query.get_or_404(id)
        m.name, m.role = request.form.get('name'), request.form.get('role')
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_event', methods=['POST'])
def add_event():
    if session.get('admin'):
        db.session.add(Event(name=request.form.get('name'), location=request.form.get('location'), time=request.form.get('time'), description=request.form.get('description')))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_event/<int:id>', methods=['POST'])
def edit_event(id):
    if session.get('admin'):
        e = Event.query.get_or_404(id)
        e.name, e.location, e.time, e.description = request.form.get('name'), request.form.get('location'), request.form.get('time'), request.form.get('description')
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if session.get('admin'):
        m_id, e_id = request.form.get('member_id'), request.form.get('event_id')
        if m_id and e_id and not Attendance.query.filter_by(member_id=m_id, event_id=e_id).first():
            db.session.add(Attendance(member_id=m_id, event_id=e_id))
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_member/<int:id>')
def delete_member(id):
    if session.get('admin'):
        db.session.delete(Member.query.get_or_404(id))
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
