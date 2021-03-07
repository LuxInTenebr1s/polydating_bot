"""Handlers modules."""

from .base import (
    AdminsFilter,
    HandlerAction,
    HandlerArgumentParser,
    OwnerFilter,
    command_handler,
    CHAT_GROUP,
    COMMON_GROUP,
    PRIVATE_GROUP,
    SHOW,
    REMOVE
)

from .private import (
    new_status as new_conv_status
)

from . import (
    base,
    common,
    private,
    public,
)

def add_handlers(dispatcher):
    """Add all modules handlers to dispatcher."""
    base.add_handlers(dispatcher)
    private.add_handlers(dispatcher)
    common.add_handlers(dispatcher)
    public.add_handlers(dispatcher)
