from flask import Flask, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup
import requests
import logging
from flask_sqlalchemy import SQLAlchemy
# from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MEALIZI'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loginn.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_company_names(limit=50):
    companies = []
    h = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'
    }
    pages = limit // 25 + (limit % 25 > 0)  # Calculate the number of pages to fetch

    for page in range(pages):
        offset = page * 25
        url = f'https://finance.yahoo.com/most-active?count=25&offset={offset}'
        logging.debug(f"Fetching URL: {url}")
        try:
            r = requests.get(url, headers=h)
            r.raise_for_status()
            content = r.text

            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table', {'class': 'W(100%)'})
            if not table:
                logging.error("Table not found on the page.")
                continue

            rows = table.find_all('tr')
            for row in rows:
                cells = row.find('a', {'class': 'Fw(600) C($linkColor)'})
                if cells:
                    company_name = cells.text.strip()
                    companies.append(company_name)
                    if len(companies) == limit:
                        break

            logging.debug(f"Found companies: {companies}")

        except requests.RequestException as e:
            logging.error(f"Failed to fetch company names: {e}")
            continue

    return companies


def analyze_company(company):
    h = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'
    }
    url = f"https://finance.yahoo.com/quote/{company}/analysis/"
    logging.debug(f"Fetching URL for analysis: {url}")
    try:
        r = requests.get(url, headers=h)
        r.raise_for_status()
        content = r.text

        soup = BeautifulSoup(content, 'html.parser')
        section = soup.find('section', {'data-testid': 'revenueEstimate'})

        company_data = {'Company': company}
        if section:
            rows = section.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if cells:
                    values = [cell.text.strip() for cell in cells]
                    if len(values) >= 4 and values[0] not in ['No. of Analysts', 'Year Ago Sales']:
                        company_data[values[0]] = values[3]

            logging.debug(f"Analyzed company data: {company_data}")
            return company_data
        else:
            logging.warning(f"Could not find revenue estimate section for company {company}")
            return None
    except requests.RequestException as e:
        logging.error(f"Failed to analyze company {company}: {e}")
        return None


@app.route('/')
@app.route('/home')
def home():
    try:
        companies = fetch_company_names(limit=50)
        if companies:
            return render_template('home.html', companies=companies)
        else:
            logging.error("No companies found.")
            return "No companies found.", 500
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500


@app.route('/company/<name>')
def company_details(name):
    try:
        company_data = analyze_company(name)
        if company_data and 'Company' in company_data:
            return render_template('company.html', company_data=company_data)
        else:
            logging.error(f"No data found for company: {name}")
            return "No data found for company.", 404
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500


@app.route('/personal')
def personal():
    try:
        companies = fetch_company_names(limit=100)
        if companies:
            return render_template('home.html', companies=companies)
        else:
            logging.error("No companies found.")
            return "No companies found.", 500
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return str(e), 500


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        new_user = User(username=uname, email=mail, password=passw)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = uname
        return redirect(url_for("personal"))
    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('personal'))
        else:
            return "Invalid credentials"
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('logout.html')


# @app.route('/user')
# def user():
#     if 'username' in session:
#         return render_template('user.html', username=session['username'])
#     return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



#lizi
