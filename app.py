import json
from random import randint, shuffle

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from forms import BookingForm, RequestForm, SortForm

app = Flask(__name__)
csrf = CSRFProtect(app)

app.config['SECRET_KEY'] = 'secret_sauce'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@127.0.0.1:5432/postgres'  # os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

goals_tutors_association = db.Table('goals_tutors',
                                    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id')),
                                    db.Column('goal_id', db.Integer, db.ForeignKey('goals.id'))
                                    )


class Tutor(db.Model):
    __tablename__ = 'tutors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    free = db.Column(db.JSON)

    goals = db.relationship('Goal', secondary=goals_tutors_association, back_populates='tutors')
    bookings = db.relationship('Booking', back_populates='tutor')


class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String)

    tutors = db.relationship('Tutor', secondary=goals_tutors_association, back_populates='goals')


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    day = db.Column(db.String, nullable=False)

    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    tutor = db.relationship('Tutor', back_populates='bookings')


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    goal = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)


week = {'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница',
        'sat': 'Суббота',
        'sun': 'Воскресенье'}


# проверка на свободые дни
def count_busy_days(schedule):
    busy_days = {}
    for day, time in schedule.items():
        for isfree in time.values():
            if not isfree:
                busy_days[day] = True
            else:
                busy_days[day] = False
    return busy_days


# создание словаря только с репетиторами с подходящей целью
def is_goal_in_tutor(goal, tutors):
    tutors_with_goal = []
    for tutor in tutors:
        for g in tutor.goals:
            if goal == g.goal:
                tutors_with_goal.append(tutor)
    return tutors_with_goal


@app.route('/')
def index():
    tutors = db.session.query(Tutor).all()
    # универсализация алгоритма случайного выбора 6-ти учителей
    first = db.session.query(Tutor).first()
    last = db.session.query(Tutor).order_by(Tutor.id.desc()).first()
    rand = []
    random_tutors = []
    for i in range(7):
        x = randint(first.id, last.id)
        if x not in rand:
            rand.append(x)
    for tutor in tutors:
        if tutor.id in rand:
            random_tutors.append(tutor)
    return render_template('index.html', tutors=random_tutors)


@app.route('/all/', methods=['GET', 'POST'])
def tutors():
    tutors = db.session.query(Tutor).all()
    if request.method == 'POST':
        sort_ids = {
            '1': 'random',
            '2': ['rating', True],
            '3': ['price', True],
            '4': ['price', False],
        }
        form = SortForm()
        sort_id = form.data['sort']
        sort_attribute = sort_ids[sort_id]
        shuffle(tutors)
        return render_template('all_sort.html',
                               tutors=tutors,
                               amount=len(tutors),
                               form=form,
                               sort_attribute=sort_attribute)
    else:
        shuffle(tutors)
        form = SortForm()
        return render_template('all.html',
                               tutors=tutors,
                               amount=len(tutors),
                               form=form)


@app.route('/goals/<goal>/')
def goal(goal):
    goals = db.session.query(Goal).all()
    tutors = db.session.query(Tutor).all()
    emoji = {"travel": "⛱", "study": "🏫", "work": "🏢", "relocate": "🚜"}
    tutors_with_goal = is_goal_in_tutor(goal, tutors)
    return render_template('goal.html',
                           goal=goal,
                           goals=goals,
                           emoji=emoji,
                           tutors=tutors_with_goal)


@app.route('/profiles/<int:id>/')
def profile(id):
    tutor = db.session.query(Tutor).get_or_404(id)
    schedule = db.session.query(Tutor).get_or_404(id).free
    busy_days = count_busy_days(json.loads(schedule))
    goals = db.session.query(Goal).all()
    return render_template('profile.html',
                           id=id,
                           tutor=tutor,
                           week=week,
                           schedule=json.loads(schedule),
                           goals=goals,
                           busy_days=busy_days)


@app.route('/request/', methods=['GET', 'POST'])
def make_request():
    request_form = RequestForm()
    if request.method == 'POST':
        name = request_form.name.data
        phone = request_form.phone.data
        purpose = request_form.purpose.data
        free_time = request_form.free_time.data
        user_request = Request(name=name, phone=phone, goal=purpose, time=free_time)
        db.session.add(user_request)
        db.session.commit()
        return render_template('request_done.html',
                               request_form=request_form,
                               name=name,
                               phone=phone,
                               purpose=purpose,
                               free_time=free_time)
    else:
        return render_template('request.html', request_form=request_form)


@app.route('/booking/<int:id>/<day>/<time>/', methods=['GET', 'POST'])
def book(id, day, time):
    booking_form = BookingForm()
    if request.method == 'POST':
        tutor = db.session.query(Tutor).get_or_404(id)
        name = booking_form.name.data
        phone = booking_form.phone.data
        user_booking = Booking(name=name, phone=phone, time=time, day=day, tutor_id=id)
        db.session.add(user_booking)
        db.session.commit()
        return render_template('booking_done.html',
                               name=name,
                               phone=phone,
                               tutor=tutor,
                               day=day,
                               time=time)
    else:
        tutor = db.session.query(Tutor).get_or_404(id)
        return render_template('booking.html',
                               id=id,
                               day=week[day],
                               time=time,
                               tutor=tutor,
                               booking_form=booking_form)


@app.errorhandler(404)
def not_found(error):
    return "Not Found", 404


if __name__ == '__main__':
    app.run()
