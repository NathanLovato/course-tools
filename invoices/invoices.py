import json
import re
import logging

# company_data = json.loads("company_data.json")
options = {
    'exclude_VAT': True,
    'currency_symbol': '€'
}


company = {
    'name': 'Test',
    'email': 'myemail@test.com',
    'address': 'My wonderful little address',
    'VAT': '98869698'
}

client = {
    'name': 'Test',
    'email': 'myemail@test.com',
    'address': 'My wonderful little address',
    'VAT': '98869698'
}

invoice_index = 1


data = {
    'company': company,
    'client': client,
    'date': '11-24-2017',
    'products': [
        {
            'name': 'A wonderful pretty little thing',
            'unit_price': 100,
        }
    ]
}



invoice_template = []
re_matches = []
with open('invoice.html', 'r') as html_doc:
    line_id = 0
    for line in html_doc:
        invoice_template.append(line)

        match = re.match(r'.+{{ (.*) }}', line)
        if match:
            re_matches.append((line_id, match.group(1)))
        line_id += 1


# TODO: store special matches like product_rows, payment_date, invoice_date
# TODO: Discard invoice_number

invoice_template_copy = invoice_template
for index, identifier in re_matches:
    string_template = '{{ ' + identifier + ' }}'
    category, key = identifier.split('_', maxsplit=1)

    try:
        replace_value = data[category][key]
    except:
        replace_value = identifier
        logging.warning('Could not find matching value for {!s}'.format(identifier))
    invoice_template_copy[index] = invoice_template_copy[index].replace(string_template, replace_value, 1)


# Create files
with open('test_output.html', 'w') as html_doc:
    html_doc.writelines(invoice_template_copy)
