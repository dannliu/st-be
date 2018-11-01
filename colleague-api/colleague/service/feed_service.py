# -*- coding:utf-8 -*-

from colleague.models.feed import Feed, FeedLike, FeedLikeStatus
from colleague.utils import encode_id


def get_feeds(uid, last_id, size):
    feeds = Feed.find_by_cursor(last_id, size)
    if len(feeds) == size:
        has_more = True
        next_cursor = encode_id(feeds[-1].id)
    json_feeds = []
    for feed in feeds:
        feed_like = FeedLike.find_by_uid(uid, feed.id)
        liked = (feed_like is not None and feed_like.status == FeedLikeStatus.Liked)
        json_feed = feed.to_dict()
        json_feed['liked'] = liked
        json_feeds.append(json_feed)
    return {
        "has_more": has_more,
        "next_cursor": next_cursor,
        "feeds": json_feeds
    }
