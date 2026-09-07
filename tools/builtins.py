from tools import files, web, system, memory_tools, documents, screen, reminders, browser, vision, automation

def register_builtin_tools(registry,memory,settings,*,models=None,automation_engine=None):
    files.register(registry)
    web.register(registry)
    system.register(registry)
    memory_tools.register(registry,memory)
    documents.register(registry)
    screen.register(registry,settings.data_dir)
    reminders.register(registry,memory)
    browser.register(registry)
    if models is not None:
        vision.register(registry,models,settings)
    if automation_engine is not None:
        automation.register(registry,automation_engine)
