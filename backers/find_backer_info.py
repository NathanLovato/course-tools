import subprocess
import sys
import csv
import logging


product_urls = {
    'premium': [
        'https://gum.co/godot-tutorial-make-professional-2d-games',
        'https://gum.co/krita-game-art-tutorial-1',
        'https://gum.co/cartoon-game-art-krita-course',
        'https://gum.co/krita-brushes-for-game-artists'
    ],
    'indie': 'https://gum.co/XEULZ',
    'hobby': 'https://gum.co/vmPA'

}

def get_csv_file_as_dict(path, skip_first_row=False, header_fields = []):
    """
    Opens a csv file and returns its content as a list,
    one list element entry per row (tuple or individual value)

    Optionally skips the header
    """
    with open(path, mode='r', encoding='utf-8') as data:
        if not header_fields:
            logging.warning('header_fields is an empty list. Using the csv file\'s first row as header.')
        reader = csv.DictReader(data, fieldnames=header_fields)
        if skip_first_row:
            next(reader)
        content = [line for line in reader]
        return content
    print('Could not open the CSV file')
    return


users_list = get_csv_file_as_dict('users.csv', skip_first_row=True, header_fields=['email', 'first_name', 'last_name', 'pledge_name',  'pledge_amount', 'coupon'])
emails_list = [user['email'] for user in users_list]

out = None
with open('temp.csv', 'w') as f:
    f.writelines([l + '\n' for l in emails_list])
with open('temp.csv', 'r') as f:
    out = subprocess.run('fzf', stdin = f, stdout = subprocess.PIPE)

search_result = out.stdout.decode('utf8').replace('\n', '')
for user in users_list:
    if user['email'] == search_result:
        print('{!s} {!s}\'s coupon code is {!s}'.format(user['first_name'].strip(), user['last_name'].strip(), user['coupon']))
        print('\n')
        if user['pledge_name'] in ['Premium', 'Craftsman\'s bundle', '1 on 1 review', 'Your own tutorial', 'Sponsor']:
            for url in product_urls['premium']:
                print(url + '/' + user['coupon'])
        elif user['pledge_name'] == 'Pro':
            print(product_urls['indie'] + '/' + user['coupon'])
        elif user['pledge_name'] == 'Essentials':
            print(product_urls['hobby'] + '/' + user['coupon'])
        break
print('\n')
