# -*- coding:utf-8 -*-

# This layer is handle cache & complex request
# We don't want to make the model layer bigger

def cursor_data(has_more, next_cursor, key, value):
    """
    Get api with cursor should have same structure
    :param has_more: Tell if has more data
    :param next_cursor: Cursor for next `get`
    :param key: map key
    :param value: map value
    :return: cursor structure
    """
    return {
        'has_more': has_more,
        'next_cursor': next_cursor,
        key: value
    }
