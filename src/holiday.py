from v10 import db

class Holiday(db.Model):
    __tablename__ = 'holidays'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    date = db.Column(db.String())

    def __init__(self, name, date):
        self.name = name
        self.date = date

    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'id': self.id, 
            'date': self.date
        }