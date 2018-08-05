from models.model_base import ModelBase


class Project(ModelBase):

    def __init__(self, name, start_year, end_year,
                 variables=None, results=None):
        self.name = name
        self.start_year = start_year
        self.end_year = end_year
        self.variables = variables or {}
        self.results = results or {}
