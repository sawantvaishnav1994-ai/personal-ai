from __future__ import annotations

import base64
from email.message import EmailMessage

from tools.registry import Risk, Tool


def register(registry, adapters):
    adapters = dict(adapters or {})

    gmail = adapters.get('gmail')
    if gmail is not None:
        registry.register(Tool(
            'gmail_list_messages',
            'List Gmail messages; params: query,max_results',
            lambda p: gmail.list_messages(
                q=str(p.get('query', ''))[:500],
                max_results=max(1, min(int(p.get('max_results', 20)), 100)),
            ),
            Risk.READ_ONLY,
        ))
        registry.register(Tool(
            'gmail_get_message',
            'Read Gmail message metadata; params: message_id',
            lambda p: gmail.get_message(str(p['message_id']), format='metadata'),
            Risk.READ_ONLY,
        ))

        def send_email(params):
            recipient = str(params['to']).strip()
            subject = str(params.get('subject', '')).strip()[:500]
            body = str(params.get('body', ''))[:100_000]
            if '@' not in recipient or any(char in recipient for char in '\r\n'):
                raise ValueError('A valid recipient email is required')
            message = EmailMessage()
            message['To'] = recipient
            message['Subject'] = subject
            message.set_content(body)
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip('=')
            return gmail.send_raw(raw)

        registry.register(Tool(
            'gmail_send_message',
            'Send an email; params: to,subject,body. Always requires owner approval.',
            send_email,
            Risk.EXTERNAL_SIDE_EFFECT,
        ))

    calendar = adapters.get('calendar')
    if calendar is not None:
        registry.register(Tool(
            'calendar_list_events',
            'List calendar events; params: calendar_id,timeMin,timeMax,maxResults',
            lambda p: calendar.list_events(
                str(p.get('calendar_id', 'primary')),
                timeMin=p.get('timeMin'),
                timeMax=p.get('timeMax'),
                maxResults=max(1, min(int(p.get('maxResults', 20)), 100)),
                singleEvents=True,
                orderBy='startTime',
            ),
            Risk.READ_ONLY,
        ))
        registry.register(Tool(
            'calendar_create_event',
            'Create a calendar event; params: event,calendar_id. Requires owner approval.',
            lambda p: calendar.create_event(dict(p['event']), str(p.get('calendar_id', 'primary'))),
            Risk.EXTERNAL_SIDE_EFFECT,
        ))
        registry.register(Tool(
            'calendar_update_event',
            'Update a calendar event; params: event_id,event,calendar_id. Requires owner approval.',
            lambda p: calendar.update_event(str(p['event_id']), dict(p['event']), str(p.get('calendar_id', 'primary'))),
            Risk.EXTERNAL_SIDE_EFFECT,
        ))
        registry.register(Tool(
            'calendar_delete_event',
            'Delete a calendar event; params: event_id,calendar_id. Requires explicit owner approval.',
            lambda p: calendar.delete_event(str(p['event_id']), str(p.get('calendar_id', 'primary'))),
            Risk.DESTRUCTIVE,
        ))

    slack = adapters.get('slack')
    if slack is not None:
        registry.register(Tool(
            'slack_read_messages',
            'Read recent Slack channel messages; params: channel,limit',
            lambda p: slack.history(str(p['channel']), max(1, min(int(p.get('limit', 50)), 100))),
            Risk.READ_ONLY,
        ))
        registry.register(Tool(
            'slack_send_message',
            'Send a Slack channel message; params: channel,text. Requires owner approval.',
            lambda p: slack.post_message(str(p['channel']), str(p['text'])[:40_000]),
            Risk.EXTERNAL_SIDE_EFFECT,
        ))

    home = adapters.get('home_assistant')
    if home is not None:
        registry.register(Tool(
            'home_assistant_read_state',
            'Read a Home Assistant entity state; params: entity_id',
            lambda p: home.state(str(p['entity_id'])),
            Risk.READ_ONLY,
        ))
        registry.register(Tool(
            'home_assistant_call_service',
            'Call a Home Assistant service; params: domain,service,data. Requires owner approval.',
            lambda p: home.call_service(str(p['domain']), str(p['service']), dict(p.get('data') or {})),
            Risk.EXTERNAL_SIDE_EFFECT,
        ))
