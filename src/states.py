from aiogram.fsm.state import State, StatesGroup

class GenStates(StatesGroup):
    prompt_wait = State() # Waiting for text prompt for generation
    edit_wait = State()   # Waiting for text prompt for editing an existing image
