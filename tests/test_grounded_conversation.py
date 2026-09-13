from agent.executor import AgentExecutor
from core.events import EventBus
from knowledge.store import KnowledgeStore
from memory.second_brain import MemoryCandidate, SecondBrain
from memory.store import MemoryStore


class Models:
    def __init__(self):
        self.plan_prompt = ''
        self.chat_system = ''
        self.sensitivity = None

    def json(self, prompt, *, system='', sensitivity='internal'):
        self.plan_prompt = prompt
        self.sensitivity = sensitivity
        return {'steps': []}

    def chat(self, prompt, *, system='', history=None, sensitivity='internal', **kwargs):
        self.chat_system = system
        self.sensitivity = sensitivity
        return 'Grounded answer [Launch facts, chunk 0]'


class Tools:
    def schema_text(self):
        return ''


def test_final_answer_receives_memory_and_cited_knowledge_context(tmp_path):
    memory = MemoryStore(tmp_path / 'memory.sqlite3')
    brain = SecondBrain(memory)
    brain.remember(MemoryCandidate(
        type='project',
        subject='Aurora',
        content='Aurora is the owner project',
        confidence=1,
        source='explicit-owner',
        verified=True,
    ))
    knowledge = KnowledgeStore(tmp_path / 'knowledge.sqlite3', tmp_path / 'objects')
    knowledge.ingest(
        filename='launch.txt',
        title='Launch facts',
        data=b'Aurora launches in Berlin.',
        source='owner-upload:test',
    )
    models = Models()
    executor = AgentExecutor(
        models=models,
        tools=Tools(),
        memory=memory,
        events=EventBus(),
        second_brain=brain,
        knowledge=knowledge,
    )

    answer = executor.chat('Where does Aurora launch?')

    assert answer.startswith('Grounded answer')
    assert 'Aurora is the owner project' in models.plan_prompt
    assert 'owner-upload:test' in models.chat_system
    assert 'Never invent a memory or citation' in models.chat_system


def test_private_knowledge_marks_model_request_sensitive(tmp_path):
    memory = MemoryStore(tmp_path / 'memory.sqlite3')
    knowledge = KnowledgeStore(tmp_path / 'knowledge.sqlite3', tmp_path / 'objects')
    knowledge.ingest(filename='private.txt', data=b'Secret launch phrase.', access_class='private')
    models = Models()
    executor = AgentExecutor(
        models=models,
        tools=Tools(),
        memory=memory,
        events=EventBus(),
        second_brain=SecondBrain(memory),
        knowledge=knowledge,
    )

    executor.chat('What is the secret launch phrase?')

    assert models.sensitivity == 'sensitive'
