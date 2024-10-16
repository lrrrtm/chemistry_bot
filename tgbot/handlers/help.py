from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.lexicon.messages import lexicon

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await message.answer(
        text=lexicon['help']['faq']
    )

