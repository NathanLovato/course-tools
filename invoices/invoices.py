import json
import subprocess
import os
import shutil
import csv
import re
import logging


# TODO: payment details
DATABASE_PATH = '2017.csv'
HTML_TEMPLATE_PATH = 'invoice.html'
OUTPUT_FOLDER = 'dist'


options = {
    'exclude_VAT': True,
    'currency_symbol': '€',
    'payment_date_delay': 60,
    'no_VAT': True
}


company = {
    'name': 'Test',
    'email': 'myemail@test.com',
    'address': 'Test',
    'VAT': '000000000'
}

# TODO: Load company from JSON

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


with open(HTML_TEMPLATE_PATH, 'r') as html_doc:
    invoice_template, re_matches = parse_html_template(html_doc)
    if not invoice_template:
        logging.error('Could not load the invoice template. Aborting operation.')
    if not re_matches:
        logging.error('Missing {{ indentifier }} templates to replace in the html template. Aborting operation.')


# TODO
def parse_invoice_date(date):
    date, payment_date = None, None

    return date, payment_date


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


def convert_invoice_to_html(invoice_data, company, invoice_index):
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

        # TODO: remove all conditional statements
        # use invoice_data[category][key] instead
        date, payment_date = parse_invoice_date(invoice_data['date'])
        if identifier == 'invoice_number':
            replace_value = "{:04d}".format(invoice_index)
        # TODO: parse date and format + calculate payment date
        elif identifier == 'invoice_date':
            replace_value = date
        elif identifier == 'payment_date':
            replace_value = payment_date
        else:
            category, key = identifier.split('_', maxsplit=1)
            try:
                replace_value = invoice_data[category][key]
            except:
                replace_value = identifier
                logging.warning('Could not find matching value for {!s}'.format(identifier))
        invoice_template_copy[index] = invoice_template_copy[index].replace(string_template, str(replace_value), 1)
    return invoice_template_copy



# prepare invoice data
invoices_database = []
with open(DATABASE_PATH, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    header = next(csv_reader)
    for row in csv_reader:
        # TODO: write functions to convert dates
        invoice_data = {
            'date': row[0],
            'client': {
                'name': row[3],
                'country_code': row[4],
                'VAT': row[5],
                'address': row[6]
            },
            'product': {
                'identifier': row[1],
                'amount': row[2] if row[2] else 1
            }
        }
        invoices_database.append(invoice_data)


# GENERATE HTML FILES
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

for index, invoice_data in enumerate( invoices_database ):
    invoice_index = index + 1
    invoice_as_html = convert_invoice_to_html(invoice_data, company, invoice_index)

    file_name = '{:04d}.html'.format(invoice_index)
    file_path = '{}/{}'.format(html_export_path, file_name)
    with open(file_path, 'w') as invoice_file:
        invoice_file.writelines(invoice_as_html)
        html_file_names.append(file_name)

# BUILD PDFs
# for name in html_file_names:
#     subprocess.run('wkhtmltopdf {}/{} {}/{}.pdf'.format(html_export_path, name, OUTPUT_FOLDER, name))
