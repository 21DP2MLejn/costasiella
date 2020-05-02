from collections import namedtuple
from graphql_relay.node.node import from_global_id
from graphql import GraphQLError

from .messages import Messages

m = Messages()


# Auth
def _check_if_user_has_permission(user, permissions):
    has_permission = False
    for p in permissions:
        if user.has_perm(p):
            has_permission = True
            break

    return has_permission


def require_login(user):
    if user.is_anonymous:
        raise GraphQLError(m.user_not_logged_in, extensions={'code': get_error_code('USER_NOT_LOGGED_IN')})


def require_permission(user, permission):
    if not user.has_perm(permission):
        raise GraphQLError(m.user_permission_denied, extensions={'code': get_error_code('USER_PERMISSION_DENIED')})


def require_login_and_permission(user, permission):
    require_login(user)
    require_permission(user, permission)


def require_login_and_one_of_permissions(user, permissions):
    require_login(user)
    
    has_permission = _check_if_user_has_permission(user, permissions)
    if not has_permission:
        raise GraphQLError(m.user_permission_denied, extensions={'code': get_error_code('USER_PERMISSION_DENIED')})


def require_login_and_one_of_permission_or_own_account(user, user_model, record_id, permissions):
    require_login(user)

    has_permission = _check_if_user_has_permission(user, permissions)
    # Check user permission
    record = user_model.objects.get(pk=record_id)
    if record.id == user.id:
        has_permission = True

    if not has_permission:
        raise GraphQLError(m.user_permission_denied, extensions={'code': get_error_code('USER_PERMISSION_DENIED')})


# To convert relay node id to real id
def get_rid(global_id):
    Rid = namedtuple('Rid', 'name id')
    return Rid(*from_global_id(global_id))


# Get file from base64 string
def get_content_file_from_base64_str(data_str, file_name):
    """
    Convert base64 encoded file to Django ContentFile
    """
    import base64
    import os
    import uuid
    from django.core.files.base import ContentFile

    file_format, file_str = data_str.split(';base64,')
    file_name, ext = os.path.splitext(file_name)

    # Add UUID to file name to prevent guessing of file names in media
    file_name = '-'.join([ file_name, str(uuid.uuid4()) ])

    return ContentFile(base64.b64decode(file_str), name='{}{}'.format(file_name, ext))


def get_error_code(error_code):
    if error_code == "USER_NOT_LOGGED_IN":
        return error_code
    elif error_code == "USER_PERMISSION_DENIED":
        return error_code