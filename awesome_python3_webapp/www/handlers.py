' url handlers '
from coreweb import get
from Model import User
import asyncio

@get('/')
def index(request):
	#logging.info('index:  __template__')
    users = yield from User.findAll()
    return {
    	'__template__': 'test.html', 
    	'users': users
    }