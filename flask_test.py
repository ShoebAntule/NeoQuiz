from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Test successful!"

if __name__ == '__main__':
    app.run(port=5501, debug=True)
