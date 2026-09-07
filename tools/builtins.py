from tools import files, web, system, memory_tools, documents, screen, reminders

def register_builtin_tools(registry, memory, settings):
    files.register(registry); web.register(registry); system.register(registry); memory_tools.register(registry,memory); documents.register(registry); screen.register(registry,settings.data_dir); reminders.register(registry,memory)
