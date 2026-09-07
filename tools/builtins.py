from tools import files,web,system,memory_tools,documents,screen,reminders,browser,vision,automation,advanced_control,notifications
def register_builtin_tools(registry,memory,settings,*,models=None,automation_engine=None,apns=None):
    files.register(registry);web.register(registry);system.register(registry);memory_tools.register(registry,memory);documents.register(registry,settings);screen.register(registry,settings.data_dir);reminders.register(registry,memory);browser.register(registry);advanced_control.register(registry,settings)
    if models is not None:vision.register(registry,models,settings)
    if automation_engine is not None:automation.register(registry,automation_engine)
    if apns is not None:notifications.register(registry,apns)
