from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Coop Job Board'

@app.get('/search')
def search():
    return 'Search'

@app.get('/jobs')
def jobs():
    return 'Jobs'


