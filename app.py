import base64
import json
import os
import random
import requests
import sys
import urllib

from flask import Flask, Response, render_template, request

app = Flask(__name__)

VALIDATION_TOKEN = os.environ.get('FB_VALDIATION_TOKEN') or 'test'
MESSENGER_PAGE_ACCESS_TOKEN = os.environ.get('MESSENGER_PAGE_ACCESS_TOKEN')


@app.route('/healthcheck')
def healthcheck():
    return Response('OK', 200)


@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return handle_get(request)
    elif request.method == 'POST':
        return handle_post(request)


def handle_get(request):
    mode = request.args.get('hub.mode')
    verify_token = request.args.get('hub.verify_token')

    response = Response(request.args.get('hub.challenge'), 200)
    if verify_token != VALIDATION_TOKEN:
        response = Response('', 403)

    return response


def handle_post(request):
    data = request.json

    if 'page' == data['object']:
        for page_entry in data['entry']:
            page_id = page_entry['id']
            timestamp = page_entry['time']

            for messaging_event in page_entry['messaging']:
                if messaging_event.get('optin'):
                    pass
                elif messaging_event.get('message'):
                    message = messaging_event.get('message')
                    text = message.get('text', '')
                    attachments = message.get('attachments', [])

                    response = requests.get('http://getbible.net/json?text=' + text)

                    if response.content == 'NULL':
                        text = 'Sorry, the Bible is not too specific on this topic.'
                    else:
                        json_response = json.loads(response.content[1:-2])

                        chapter = ''
                        book_nr = random.choice(json_response['book'].keys())
                        verse_keys = map(str, sorted(map(int, json_response['book'][book_nr]['chapter'].keys())))
                        verse_key = random.choice(verse_keys)
                        text = json_response['book'][book_nr]['chapter'][verse_key]['verse']

                    respond(messaging_event['sender']['id'], text)
                elif messaging_event.get('delivery'):
                    # Handle message delivery
                    pass
                elif messaging_event.get('postback'):
                    # Handle postback
                    pass
                elif messaging_event.get('read'):
                    # Handle read
                    pass
                elif messaging_event.get('account_linking'):
                    # Handle account linking
                    pass
                else:
                    # Unknown message
                    pass

    return Response('', 200)


def respond(recipient_id, text, buttons=None):
    payload = {
        'recipient': {
            'id': recipient_id,
        },
        'message': {
            'text': text,
        }
    }

    response = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token={access_token}'.format(
        access_token=MESSENGER_PAGE_ACCESS_TOKEN
    ), data=json.dumps(payload), headers={
        'content-type': 'application/json'
    })

    print response.__dict__
