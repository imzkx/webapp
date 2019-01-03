#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio,logging

import aiomysql

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

@asyncio.coroutine
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

@asyncio.coroutine
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

@asyncio.coroutine
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

def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)


class Filed(object):
    """docstring for Filed"""
    def __init__(self, name, colume_type, primary_key, default):
        self.name = name
        self.colume_type = colume_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s, %s>' %(self.__class__.__name__, self.colume_type,self.name)


class StringFiled(Filed):
    """docstring for StringFiled"""
    def __init__(self, name = None, primary_key = False, default = None, ddl = 'varchar(100)'):
        super().__init__(name, ddl, primary_key, default)

class BooleanFiled(Filed):
    """docstring for StringFiled"""
    def __init__(self, name= None, default = False):
        super().__init__(name, 'boolean', False, default)

class FloatFiled(Filed):
    """docstring for StringFiled"""
    def __init__(self, name = None, primary_key = False, default = 0):
        super().__init__(name, 'bigint', primary_key, default)

class TextFiled(Filed):
    """docstring for StringFiled"""
    def __init__(self, name = None, primary_key = False, default = None):
        super().__init__(name, 'text', primary_key, default)


class ModelMetaclass(type):
    """docstring for ModelMetaclass"""
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Filed):
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey=k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fileds = list(map(lambda f: '%s' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields

        attrs['__select__'] = 'select %s, %s from %s' % (primaryKey, ','.join(escaped_fileds), tableName)
        attrs['__insert__'] = 'insert into %s (%s, %s) values (%s)' %(tableName, ','.join(escaped_fileds), primaryKey, create_args_string(len(escaped_fileds)+1))
        attrs['__update__'] = 'update %s set %s where %s = ?' % (tableName, ','.join(map(lambda f: '%s=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from %s where %s' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    """docstring for Model"""
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Modle' obj has no attribute '%s'" % key)
        else:
            pass
        finally:
            pass

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueorDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default

                logging.debug('using default value for %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        'find boject by primary key'
        rs = yield select('%s where %s=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueorDefault, self.__fields__))
        args.append(self.getValueorDefault(self.__primary_key__))
        rows = yield excute(self.__insert__, args)
        if rows != 1:
            logging.warn('Failed to insert record: affected rows:%s' % rows)

