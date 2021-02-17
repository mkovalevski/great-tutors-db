import json

from app import db, Tutor, Goal


def seed_tutors(data):
    tutors = []
    for teacher in data['teachers']:
        tutor = Tutor(name=teacher['name'],
                      about=teacher['about'],
                      rating=teacher['rating'],
                      picture=teacher['picture'],
                      price=teacher['price'],
                      free=teacher['free'])
        tutors.append(tutor)
        for goal in db.session.query(Goal).all():
            if goal.goal in teacher['goals']:
                goal.tutors.append(tutor)
    db.session.bulk_save_objects(tutors)
    db.session.commit()


def seed_goals(data):
    goals = []
    for g in data:
        goal = Goal(goal=g)
        goals.append(goal)
    db.session.bulk_save_objects(goals)
    db.session.commit()


def main():
    with open('data.json') as f:
        data = json.load(f)
    seed_goals(data['goals'])
    seed_tutors(data)


if __name__ == '__main__':
    main()
