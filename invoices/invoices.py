import json
import subprocess
import os
import csv
import re
import logging

DATABASE_PATH = '2017.csv'
HTML_TEMPLATE_PATH = 'invoice.html'
OUTPUT_FOLDER = 'dist'


# TODO: product_rows, total, payment_date, payment_details
# TODO: copy img/ and .css file to dist/ if necessary
# TODO: convert to html with wkhtmltopdf

options = {
    'exclude_VAT': True,
    'currency_symbol': '€',
    'payment_date_delay': 60
}


invoice_index = 1
company = {
    'name': 'Test',
    'email': 'myemail@test.com',
    'address': 'My wonderful little address',
    'VAT': '98869698'
}


product_database = []

# PARSE HTML TEMPLATE
def parse_html_template(file_path):
    invoice_template, re_matches = [], []
    replace_total_matches = {}
    replace_products_line = None
    with open(file_path, 'r') as html_doc:
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
                elif identifier.startswith('total'):
                    replace_total_matches[match.group(1)] = line_id
                elif identifier == 'product_rows':
                    replace_products_line = line_id
                else:
                    re_matches.append((line_id, match.group(1)))
            invoice_template.append(line)
            line_id += 1
    return invoice_template, re_matches, replace_total_matches, replace_products_line

invoice_template, re_matches, replace_total_matches, replace_products_line = parse_html_template(HTML_TEMPLATE_PATH)
if not invoice_template:
    logging.error('Could not load the invoice template. Aborting operation.')
if not re_matches:
    logging.error('Missing {{ indentifier }} templates to replace in the html template. Aborting operation.')


# TODO: store special matches like product_rows, payment_date, invoice_date?
# TODO: Discard invoice_number

def convert_invoice_to_html(invoice_data, company):
    invoice_template_copy = invoice_template
    for index, identifier in re_matches:
        string_template = '{{ ' + identifier + ' }}'

        if identifier == 'invoice_number':
            replace_value = "{:04d}".format(invoice_index)
        else:
            category, key = identifier.split('_', maxsplit=1)
            try:
                replace_value = invoice_data[category][key]
            except:
                replace_value = identifier
                logging.warning('Could not find matching value for {!s}'.format(identifier))
        invoice_template_copy[index] = invoice_template_copy[index].replace(string_template, replace_value, 1)

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


html_file_names = []
html_export_path = '{!s}/html'.format(OUTPUT_FOLDER)
if not os.path.exists(html_export_path):
    os.makedirs(html_export_path)
for invoice_data in invoices_database:
    invoice_as_html = convert_invoice_to_html(invoice_data, company)
    file_name = '{:04d}.html'.format(invoice_index)
    file_path = '{}/{}'.format(html_export_path, file_name)
    with open(file_path, 'w') as invoice_file:
        invoice_file.writelines(invoice_as_html)
        html_file_names.append(file_name)
        invoice_index += 1

for name in html_file_names:
    subprocess.run('wkhtmltopdf {}/{} {}/{}.pdf'.format(html_export_path, name, OUTPUT_FOLDER, name))
