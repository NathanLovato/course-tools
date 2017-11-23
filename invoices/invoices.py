import json
import re

# company_data = json.loads("company_data.json")

data = {
}

company = {
    'name': 'Lovato Nathan',
    'email': 'nathan@gdquest.com',
    'address': '81 Place de la Mairie, 74550 Perrignier',
    'VAT': 'FR09801047630',
}

client = {
    'name': 'Lovato Nathan',
    'email': 'test\@test.org',
    'address': '81 Place de la Mairie, 74550 Perrignier',
    'VAT': 'FR09801047630',
}

products: [
    {
        'id': 44,
        'name': 'Cours Krita Pro',
        'unit_price': 60,
        'amount': 1
    }
]

with open('invoice.html', 'r') as html_doc:
    for line in html_doc:
        match = re.match(r'.+{{ (.*) }}', line)
        if match:
            print(match.group(1))
