# -*- coding:utf-8 -*-

from flask_jwt_extended import current_user
from flask_restful import reqparse, Resource, request

from colleague.acl import login_required
from colleague.models.feed import Feed, FeedLike, FeedLikeStatus
from colleague.models.meida import Image
from colleague.service import feed_service
from colleague.utils import decode_id, st_raise_error, ErrorCode
from . import compose_response


class ApiFeed(Resource):

    @login_required
    def post(self):
        text = request.json.get('text')
        encoded_image_ids = request.json.get('images')
        if not text and not encoded_image_ids:
            st_raise_error(ErrorCode.FEED_CONTENT_INCOMPLETE)
        image_ids = None
        if encoded_image_ids:
            image_ids = [Image.decode_id(id) for id in encoded_image_ids]
        feed = Feed(uid=current_user.user.id, images=image_ids, text=text)
        Feed.add(feed)
        new_feed = Feed.find(feed.id)
        return compose_response(result=new_feed.to_dict(), message="发布成功")

    @login_required
    def get(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('cursor', type=unicode, location='args', required=False)
        args = reqparser.parse_args()
        cursor = args.get('cursor')
        last_id = int(decode_id(cursor)) if cursor else None
        feeds = feed_service.get_feeds(current_user.user.id, last_id, 20)
        return compose_response(result=feeds)


class ApiFeedLike(Resource):

    @login_required
    def post(self):
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('feed_id', type=unicode, location='json', required=False)
        args = reqparser.parse_args()
        feed_id = int(decode_id(args.get('feed_id')))
        feed = Feed.find(feed_id)
        if not feed:
            st_raise_error(ErrorCode.FEED_NOT_FOUND)
        feed_like = FeedLike.find_by_uid(current_user.user.id, feed_id)
        if not feed_like:
            feed_like = FeedLike(uid=current_user.user.id, feed_id=feed_id,
                                 status=FeedLikeStatus.Liked)
            FeedLike.add(feed_like)
        else:
            feed_like.status = FeedLikeStatus.reverse(feed_like.status)
        if feed_like.status == FeedLikeStatus.Liked:
            feed.like_count += 1
        else:
            feed.like_count -= 1
        if feed.like_count < 0:
            # Ensure the count is >= 0
            feed.like_count = 0
        feed.update()
        return compose_response(result=feed.to_dict())
