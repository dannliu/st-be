# -*- coding:utf-8 -*-

tables = ['organizations', 'work_experience', 'users', 'endorsement',
          'endorse_comment', 'contact', 'contact_request', 'image',
          'feed', 'feed_like', 'user_endorse']

if __name__ == "__main__":
    assert (len(tables) == 11)
    for table in tables:
        print "COPY(select * from {0}) TO '/tmp/{0}.sql';".format(table)
    print("\n\n")
    for table in tables:
        print "load data infile '/tmp/{0}.sql' into table {0} fields terminated by '\\t' lines terminated by '\\n';".format(table)
