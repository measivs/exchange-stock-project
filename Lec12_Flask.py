from flask import Flask, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup
import requests
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HelloBTU'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_company_names(limit=50):
    companies = []
    h = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'
    }
    url = f'https://finance.yahoo.com/most-active?count={limit}&offset=0'
    logging.debug(f"Fetching URL: {url}")
    try:
        r = requests.get(url, headers=h)
        r.raise_for_status()
        content = r.text

        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table', {'class': 'W(100%)'})
        if not table:
            logging.error("Table not found on the page.")
            return []

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find('a', {'class': 'Fw(600) C($linkColor)'})
            if cells:
                company_name = cells.text.strip()
                companies.append(company_name)
                if len(companies) == limit:
                    break

        logging.debug(f"Found companies: {companies}")
        return companies
    except requests.RequestException as e:
        logging.error(f"Failed to fetch company names: {e}")
        return []


def analyze_company(company):
    h = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.4; en-gb; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'
    }
    url = f"https://finance.yahoo.com/quote/{company}/analysis/"
    logging.debug(f"Fetching URL for analysis: {url}")
    try:
        r = requests.get(url, headers=h)
        r.raise_for_status()  # Raise HTTPError for bad responses
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
        companies = fetch_company_names(limit=5)
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


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        session['username'] = email
        return redirect(url_for('user'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('logout.html')


@app.route('/user')
def user():
    if 'username' in session:
        return render_template('user.html', username=session['username'])
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
