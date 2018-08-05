import click
import json
import random
from models.project import Project
from models.model_base import to_json


def generate_variables(start_year, end_year):
    return {
        'Production': {i: random.randint(1000, 10000)
                       for i in range(start_year, end_year)},
        'Cost': {i: random.randint(50000, 600000)
                 for i in range(start_year, end_year)}
    }


def generate_project(index):
    duration = random.randint(20, 80)
    start_year = random.randint(2012, 2020)
    end_year = start_year + duration
    project = Project(
        name=f'Project {index}',
        start_year=start_year,
        end_year=end_year,
        variables=generate_variables(start_year, end_year)
    )
    return project


@click.command()
@click.option('--count', default=100)
@click.option('--filename', default=None)
def generate(count, filename):
    if not filename:
        filename = f'C:/data/{count}Projects.json'
    projects = []
    for i in range(count):
        project = generate_project(i)
        projects.append(project)

    data = {'count': len(projects),
            'projects': projects}
    try:
        with open(filename, 'wt') as file:
            file.write(json.dumps(to_json(data), sort_keys=True, indent=4))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    generate()
