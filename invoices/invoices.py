# -*- coding: utf-8 -*-
import json
import subprocess
import os
import shutil
import csv
import re
import logging
import locale
import datetime
import sys


DATABASE_PATH = '2017.csv'
HTML_TEMPLATE_PATH = 'invoice.html'
OUTPUT_FOLDER = 'dist'

locale.setlocale(locale.LC_TIME, 'fr')
DATE_FORMAT = '%d %B %Y'


options = {
    'exclude_VAT': True,
    'default_currency': 'EUR',
    'payment_date_delay': 60,
    'no_VAT': True,
    'payment_options': {
        'paypal': '',
        'wire': ''
    }
}

company = {
    'name': 'Empty',
    'email': 'empty@test.com',
    'address': 'Empty',
    'VAT': '000000000'
}

def parse_invoice_date(date_string):
    date, payment_date = None, None

    # PayPal csv date format: mm/dd/yyyy
    date = datetime.datetime.strptime(date_string, '%m/%d/%Y')
    payment_date = date.now() + datetime.timedelta(days=options['payment_date_delay'])

    return date, payment_date



# PARSE HTML TEMPLATE
def parse_html_template(html_doc):
    invoice_template, re_matches = [], []

    line_id = 0
    for line in html_doc:
        match = re.match(r'.+{{ (.*) }}', line)
        if match:
            identifier = match.group(1)

            # Pre-replace company details
            if identifier.startswith('company'):
                category, key = identifier.split('_', maxsplit=1)
                string_template = '{{ ' + identifier + ' }}'
                line = line.replace(string_template, company[key], 1)
            else:
                re_matches.append((line_id, match.group(1)))
        invoice_template.append(line)
        line_id += 1

    return invoice_template, re_matches



def get_product_from_id(product_id):
    product = {}

    if product_id.isdigit():
        index = int(product_id)
        product = product_database[index]
    else:
        for index, name in enumerate(product_names):
            if product_id == name:
                product = product_database[index]

    if not product:
        logging.warning('Could not find product id {!s}, returning None'.format(product_id))
    return product



def convert_invoice_to_html(invoice_data, company):
    invoice_template_copy = list(invoice_template)

    # PRODUCT
    # TODO: to support multiple products, parse products in a separate function
    # Use a separate html template (one <tr> per product)
    # return the full list of <tr> as a string to replace {{ product_rows }}
    total_tax_excl, total_VAT = 0, 0

    product_data = invoice_data['product']
    amount = product_data['amount']
    product = get_product_from_id(product_data['identifier'])

    VAT_rate = 0 if options['no_VAT'] == True else product['VAT_rate']
    product_cost_tax_excl = product['unit_price'] * amount
    product_VAT = product_cost_tax_excl * VAT_rate

    total_tax_excl += product_cost_tax_excl
    total_VAT += product_VAT

    # TODO: refactor invoice into object
    invoice_data['product']['name'] = product['name']
    invoice_data['product']['unit_price'] = product['unit_price']
    invoice_data['product']['VAT_rate'] = VAT_rate
    invoice_data['product']['total_tax_excl'] = product_cost_tax_excl

    invoice_data['total'] = {}
    invoice_data['total']['discount'] = 0
    invoice_data['total']['excl_tax'] = total_tax_excl
    invoice_data['total']['tax'] = total_VAT
    invoice_data['total']['incl_tax'] = total_tax_excl + total_VAT

    # REPLACE VALUES
    for index, identifier in re_matches:
        string_template = '{{ ' + identifier + ' }}'
        category, key = identifier.split('_', maxsplit=1)
        try:
            replace_value = invoice_data[category][key]
        except:
            replace_value = identifier
            logging.warning('Could not find matching value for {!s}'.format(identifier))
        if identifier in ['product_unit_price', 'product_total_tax_excl', 'total_discount', 'total_excl_tax', 'total_tax', 'total_incl_tax']:
            replace_value = str(replace_value) + invoice_data['invoice']['currency']
        invoice_template_copy[index] = invoice_template_copy[index].replace(string_template, str(replace_value), 1)
    return invoice_template_copy



def get_currency_symbol(currency):
    # USE HTML NAME CODES
    currencies = {
        'EUR': '&euro;',
        'USD': '$',
        'JPY': ''
    }
    return currencies[currency]



def get_payment_details(option):
    option_string = option.lower()
    if not option_string in options['payment_options'].keys():
        return ''
    return options['payment_options'][option_string]


# Parse options
# TODO: move options and payment details to a JSON file
# and parse the bank-details template like the invoice one
try:
    with open('config.json') as json_doc:
        config = json.loads(json_doc.read())
        options['payment_options']['paypal'] = 'PayPal address: ' + config['paypal']

        company['name'] = config['company']['name']
        company['email'] = config['company']['email']
        company['address'] = config['company']['address']
        company['VAT'] = config['company']['VAT']
except FileNotFoundError:
    logging.warning('Missing config.json file. Invoices will use default options.')

with open('bank-details.html') as html_doc:
    options['payment_options']['wire'] = html_doc.read()


# Parse product database
product_database = []
product_names = []
with open('products.csv', 'r') as csv_file:
    reader = csv.reader(csv_file)
    header = next(reader)

    product = {}
    for row in reader:
        product_names.append(row[0])
        product['name'] = row[0]
        product['unit_price'] = int(row[1])
        product['VAT_rate'] = int(row[2]) / 100
        product_database.append(product)


with open(HTML_TEMPLATE_PATH, 'r') as html_doc:
    invoice_template, re_matches = parse_html_template(html_doc)
    if not invoice_template:
        logging.error('Could not load the invoice template. Aborting operation.')
    if not re_matches:
        logging.error('Missing {{ indentifier }} templates to replace in the html template. Aborting operation.')


# prepare invoice data
invoices_database = []
with open(DATABASE_PATH, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    header = next(csv_reader)

    # TODO: Convert to dict, it's not readable
    for index, row in enumerate(csv_reader):
        invoice_index = index + 1
        date, payment_date = parse_invoice_date(row[0])
        currency = row[1] if row[1] else options['default_currency']
        invoice_data = {
            'client': {
                'name': row[4],
                'country_code': row[5],
                'VAT': row[6],
                'address': row[7]
            },
            'product': {
                'identifier': row[2],
                'amount': row[3] if row[3] else 1
            },
            'invoice': {
                'number': "{:04d}".format(invoice_index),
                'date': date.strftime(DATE_FORMAT),
                'currency': get_currency_symbol(currency)
            },
            'payment': {
                'date': payment_date.strftime(DATE_FORMAT),
                'details': get_payment_details(row[8])
            }
        }
        invoices_database.append(invoice_data)



# HTML FILES
html_file_names = []
html_export_path = '{!s}/html'.format(OUTPUT_FOLDER)

# Create directories and copy files
if not os.path.exists(html_export_path):
    os.makedirs(html_export_path)
css_output_path = os.path.join(html_export_path, 'style.css')
if not os.path.exists(css_output_path):
    shutil.copy('style.css', css_output_path)
img_output_path = os.path.join(html_export_path, 'img')
if not os.path.exists(img_output_path):
    shutil.copytree('img', img_output_path)

# Generate html files
for invoice_data in invoices_database:
    invoice_as_html = convert_invoice_to_html(invoice_data, company)

    # TODO: name invoices by date and place in folder per month?
    # e.g. dist/.../yyyy/mm-dd-0001.html
    file_name = '{}.html'.format(invoice_data['invoice']['number'])
    print(file_name)
    file_path = '{}/{}'.format(html_export_path, file_name)
    with open(file_path, 'w') as invoice_file:
        invoice_file.writelines(invoice_as_html)
        html_file_names.append(file_name)

# BUILD PDFs
for name in html_file_names:
    subprocess.run('wkhtmltopdf {}/{} {}/{}.pdf'.format(html_export_path, name, OUTPUT_FOLDER, name))
