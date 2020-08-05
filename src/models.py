from v10 import db

class Holiday(db.Model):
    __tablename__ = 'holidays'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    date = db.Column(db.String())
    ibge_code = db.Column(db.Integer())

    def __init__(self, name, date, ibge_code):
        self.name = name
        self.date = date
        self.ibge_code = ibge_code

    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'name': self.name
        }