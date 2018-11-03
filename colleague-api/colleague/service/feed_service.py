# -*- coding:utf-8 -*-

from colleague.models.feed import Feed, FeedLike, FeedLikeStatus
from colleague.models.meida import Image
from colleague.utils import encode_id


def get_feeds(uid, last_id, size):
    feeds = Feed.find_by_cursor(last_id, size)
    has_more = False
    next_cursor = None
    if len(feeds) == size:
        has_more = True
        next_cursor = encode_id(feeds[-1].id)
    dict_feeds = []
    for feed in feeds:
        feed_like = FeedLike.find_by_uid(uid, feed.id)
        liked = (feed_like is not None and feed_like.status == FeedLikeStatus.Liked)
        dict_feed = feed.to_dict()
        dict_feed['liked'] = liked
        if feed.images:
            images = [image.to_dict() for image in Image.find_by_ids(feed.images)]
            dict_feed['images'] = images
        dict_feeds.append(dict_feed)
    return {
        "has_more": has_more,
        "next_cursor": next_cursor,
        "feeds": dict_feeds
    }
