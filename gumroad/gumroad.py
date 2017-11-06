"""
Shell program to manage Gumroad products by sending http requests.

Call the script with like `python gumroad.py mode gumroad_option -options`

`mode` is one of three keywords: `get`, `post` and `delete`, to respectively download, create and delete data.
`gumroad_option` is the part of your shop you want to work on: currently `coupons` or `products`

Access token:
You need an access token to connect with the Gumroad servers via the script. Either store it in a file named access_token next to the script or call the script with the --access-token option.

`python gumroad.py get products --access-token 'your_access_token'`


Batch-create coupon codes:
`python gumroad.py post coupons --csv 'path/to/csv_file' -product 'name or id (partial works)'`


Batch create coupon codes: python gumroad.py post coupons
"""
import os
import sys
import csv
import json
import requests
import time
import argparse
from enum import Enum

import logging

PRODUCT_URL = 'https://api.gumroad.com/v2/products/'


class Tiers(Enum):
    HOBBY = 0
    INDIE = 1
    PRO = 2

PRODUCTS_FILE = 'products.csv'
if not os.path.exists(PRODUCTS_FILE):
    logging.warning('Missing products.csv file')


class ProductKeys(Enum):
    NAME = 'name'
    ID = 'id'
    SHORT_URL = 'short_url'

PRODUCT_KEYS = [member.value for member in ProductKeys]

products = []
with open(PRODUCTS_FILE) as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    header = next(reader)
    for row in reader:
        product = dict(zip(header, row))
        products.append(product)

print('Available products:', '\n')
for p in products:
    print("{!s}: {!s}".format(p[ProductKeys.NAME.value], p[ProductKeys.ID.value]))
print('\n')


class Modes(Enum):
    GET = 'get'
    POST = 'post'
    DELETE = 'delete'


class GumroadOptions(Enum):
    PRODUCTS = 'products'
    COUPONS = 'coupons'


MODES = [member.value for member in Modes]
GUMROAD_OPTIONS = [member.value for member in GumroadOptions]

def get_cli_arguments():
    """
    Returns a tuple of args, mode, option.
    args is the raw list of arguments parsed by argparse
    mode and option are respectively members of the Modes and GumroadOptions Enums
    """
    parser = argparse.ArgumentParser(description='Manage products and coupon codes on Gumroad')

    # Positional arguments
    parser.add_argument('mode', choices=MODES, default=Modes.GET.value, help='Choose a mode between {!s}. Get retrieves and stores data from gumroad, post creates new entries and delete deletes them. Default: {!s}'.format(MODES, Modes.GET))
    parser.add_argument('option', type=str, choices=GUMROAD_OPTIONS, default=GumroadOptions.COUPONS.value, help='Select what to edit or retrieve data from between {!s}. Default: {!s}'.format(GUMROAD_OPTIONS, GumroadOptions.COUPONS.value))

    # Options
    parser.add_argument('-c', '--csv', type=str, default='', help='csv file to pull data from. One id or coupon per line')
    parser.add_argument('-at', '--access_token', type=str, default='', help='Gumroad API access_token. You can find it in your account settings on gumroad.com')
    parser.add_argument('-pi', '--product_id', type=str, default='', help='The id or the name of the product you want to work on.')

    args = parser.parse_args()
    mode = [member for member in Modes if args.mode == member.value][0]
    option = [member for member in GumroadOptions if args.option == member.value][0]

    return args, mode, option


def create_coupon_request(product_id, name, amount_off, offer_type='percent', max_purchase_count='1', universal='false'):
    """
    Returns a tuple of url(string), data(dict) ready to send a POST request to generate a new coupon code and wraps it with the app's access token.
    All passed args must be text strings.

    Args:
    - product_id, pass a valid Gumroad product id ()
    - name, offer code's name and url slug
    - amount_off, the amount off (in currency or percent, based on offer_type)
    - offer_type, must be 'cent' or 'percent'
    - max_purchase_count, max uses for this offer code
    - universal, 'true' applies to all products, 'false only applies to the current product
    """
    url = PRODUCT_URL + product_id + '/offer_codes/'
    data = {
        'access_token': access_token,
        'product_id': product_id,
        'name': name,
        'amount_off': amount_off,
        'offer_type': offer_type,
        'max_purchase_count': max_purchase_count,
        'universal': universal
    }
    return (url, data)


def download_products_data():
    """
    Returns a dictionary of product name: { data_dict } and the total products count
    """
    r = requests.get('https://api.gumroad.com/v2/products', data={'access_token': access_token})
    import json
    data = r.json()

    products = []
    for p in data['products']:
        p_dict = {
            'name': p['name'],
            'id': p['id'],
            'short_url': p['short_url']
        }
        products.append(p_dict)
    total = len(data['products'])
    return products, total


def recreate_coupon(product_code, coupon_code):
    """
    Deletes a coupon if it exists and re-creates it.
    Use to re-create a coupon when a user didn't use it right or didn't
    save the product in his Gumroad library
    Returns None
    """
    delete_url = PRODUCT_URL + product_code + '/offer_codes/' + coupon_code
    r = requests.delete(delete_url, data={'access_token': ACCESS_TOKEN}  )
    url, data = create_coupon_request(product_code, coupon_code, '100')
    r = requests.post(url, data)


def get_csv_file_as_list(path, header=False):
    """
    Opens a csv file and returns its content as a list,
    one list element entry per row (tuple or individual value)

    Optionally skips the header
    """
    with open(path, mode='r', encoding='utf-8') as data:
        reader = csv.reader(data)
        if header:
            next(reader)
        content = [line for line in reader]
        return content
    print('Could not open the CSV file')
    return


def batch_create_coupons(coupon_codes, product_id):
    total_lines = len(coupon_codes)
    current_progress = 0

    # Generate new coupons
    for line in coupon_codes:
        if line == '':
            continue
        url, data = create_coupon_request(product_id, line, '100')
        r = requests.post(url, data)
        current_progress += 1
        print("\rProgress: {!s}/{!s}".format(current_progress, total_lines),
            end="",
            flush=True)



args, mode, option = get_cli_arguments()

access_token = None
with open('access_token', mode='r') as content:
    access_token = content.readline().strip()

if not access_token:
    if not args.access_token:
        print('Missing Gumroad API access token. Put it in a file named access_token next to the script or use the --access_token option when you call the script from the shell.')
        sys.exit()
    access_token = args.access_token

def get_product_product_id(identifier):
    """
    Searches the product in the list by id or by name
    Returns None if it can't find the product
    """
    identifier = identifier.rstrip()
    for product in products:
        name = product['name'].rstrip()
        if identifier == name or identifier == product['id'].rstrip():
            return product['id']
    return None


# SCRIPT
# Create coupons
product_id = None
if mode is Modes.POST:
    if args.product_id:
        product_id = get_product_product_id(args.product_id)
        if product_id is None:
            print("Couldn't find the product id or name.")
    else:
        print('No valid product id or name passed with the --product_id option.')
    while product_id is None:
        user_input = input('Please enter a valid product name or id (list above): ')
        product_id = get_product_product_id(user_input)


if mode is Modes.POST and option is GumroadOptions.COUPONS:
    if not os.path.exists(args.csv):
        print('Could not find the csv file')
        sys.exit()

    csv_data = get_csv_file_as_list(args.csv)
    batch_create_coupons(csv_data, product_id)

if mode is Modes.GET and option is GumroadOptions.PRODUCTS:
    products, total_count = download_products_data()
    print('There are {!s} products in total'.format(total_count))

    with open('products.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        header = PRODUCT_KEYS
        writer.writerow(header)

        for product in products:
            row = [product[key] for key in product.keys()]
            writer.writerow(row)

# delete coupons
# Get coupon list
# extract tuples of name: id so you can use the id to send a delete request
# open the csv file and compare each entry to the names
# delete if match found
# url, data = create_coupon_request(PRODUCT_IDS.MAKE_PROFESSIONAL_2D_GAMES_WITH_GODOT, '', '100')
# r = requests.get(url, data)
# response_dict = json.loads(r.text)
# count = 0

# coupon_names = [coupon['name'].replace('\ufeff', '') for coupon in response_dict['offer_codes']]
# with open(csv_file, mode='r', encoding='utf-8') as data:
#     reader = csv.reader(data)
#     for line in reader:
#         coupon_name = str(line[2])
#         url, data = create_coupon_request(PRODUCT_IDS.MAKE_PROFESSIONAL_2D_GAMES_WITH_GODOT, coupon_name, '100')
#         r = requests.post(url, data)
# sys.exit()
