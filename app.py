from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "VIP Number Backend is Live!"

if __name__ == '__main__':
    app.run()
