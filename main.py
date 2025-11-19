# main.py
from flask import Flask

# 1. تعریف شیء برنامه - Gunicorn به این نیاز دارد
app = Flask(__name__) 

@app.route("/")
def hello_world():
    # 2. بجای print، پاسخ HTTP برگردانید
    return "Hello from Render!" 

# (قسمت پایین ضروری نیست اما متداول است)
# if __name__ == "__main__":
#     app.run()