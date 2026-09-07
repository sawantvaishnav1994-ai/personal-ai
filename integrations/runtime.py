from integrations.registry import IntegrationRegistry,Integration
from integrations.adapters import GmailAdapter,GoogleCalendarAdapter,SlackAdapter,HomeAssistantAdapter
def build_integrations(settings):
    reg=IntegrationRegistry(); adapters={}
    if settings.gmail_token:
        a=GmailAdapter(settings.gmail_token); adapters['gmail']=a; reg.register(Integration('gmail','Gmail',{'read_mail','send_mail'},lambda:bool(a.list_messages(max_results=1) is not None)))
    if settings.calendar_token:
        a=GoogleCalendarAdapter(settings.calendar_token); adapters['calendar']=a; reg.register(Integration('calendar','Google Calendar',{'read_events','create_event'},lambda:bool(a.list_events(maxResults=1) is not None)))
    if settings.slack_token:
        a=SlackAdapter(settings.slack_token); adapters['slack']=a; reg.register(Integration('slack','Slack',{'read_messages','send_message'},lambda:bool(a.auth_test())))
    if settings.home_assistant_url and settings.home_assistant_token:
        a=HomeAssistantAdapter(settings.home_assistant_url,settings.home_assistant_token); adapters['home_assistant']=a; reg.register(Integration('home_assistant','Home Assistant',{'read_state','call_service'},lambda:bool(a.states() is not None)))
    return reg,adapters
