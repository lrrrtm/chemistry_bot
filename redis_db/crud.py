import redis

from os import getenv
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    return redis.Redis(host=getenv('REDIS_HOST'), port=getenv('REDIS_PORT'), password=getenv('REDIS_PASSWORD'), db=0)


def set_temporary_key(key, value, expire_time: int = 300):
    with create_connection() as rd:
        rd.setex(name=key, value=value, time=expire_time)


def get_value(key):
    with create_connection() as rd:
        return rd.get(key)


def delete_key(key):
    with create_connection() as rd:
        rd.delete(key)