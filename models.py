from v10 import db

"""
    Definition of a Holiday object model in the database
"""
class Holiday(db.Model):
    __tablename__ = 'holidays'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    date = db.Column(db.String())
    ibge_code = db.Column(db.Integer())
    type_ = db.Column(db.String())

    def __init__(self, name, date, ibge_code, type_):
        self.name = name
        self.date = date
        self.ibge_code = ibge_code
        self.type_ = type_

    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            "name": self.name
        }