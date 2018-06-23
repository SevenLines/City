from back.base import db


class Frames(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idx = db.Column(db.Integer)
    l = db.Column(db.Float)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    lng = db.Column(db.Float)
    lat = db.Column(db.Float)
    alt = db.Column(db.Float)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=True)
    frame = db.Column(db.Integer)
    point = db.Column()

    done = db.Column(db.Boolean)


class Roads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.Text)
    road_id = db.Column(db.Integer)

    frames = db.relationship('Frames', backref='video', lazy=True)
