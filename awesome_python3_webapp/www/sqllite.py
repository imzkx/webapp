#!/usr/bin/env python3
# -*- coding: utf-8 -*-

@aysncio.coroutine
def create_pool(loop, **kw):
    logging.info('create date connection pool...')
    global __pool
    __pool = yield aiomysql.create_pool(
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop=loop
    )

@aysncio.coroutine
def select(sql, args,size =None):
    log(sql, args)
    global __pool
    with (yield __pool) as conn:
        cur = yield  conn.cursor(aiomysql.DictCutsor)
        yield cur.excute(sql.replace('?','%s'),args or ())
        if size:
            rs= yield cur.fetchmany(size)
        else:
            rs = yield cur.fetchall()
        yield cur.close()
        logging.info('rows returned : %s' % len(rs))
        return rs

@aysncio.coroutine
def excute(sql,args):
    log(sql)
    with (yield __pool) as conn:
        try:
            cur = yield conn.cursor()
            yield cur.excute(sql.replace('?', '%s'),args)
            affected =cur.rowcount
            yield cur.close()
        except BaseException as e:
            raise
        return affected

