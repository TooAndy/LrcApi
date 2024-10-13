import logging
import urllib
import requests

from . import *

from flask import request, abort, jsonify, render_template_string
from urllib.parse import unquote_plus

from mod.auth import webui
from mod.auth.authentication import require_auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
    'origin': 'https://music.163.com',
    'referer': 'https://music.163.com',
}

COMMON_SEARCH_URL_WANGYI = 'https://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={}&type={}&offset={}&total=true&limit={}'
ARTIST_SEARCH_URL = 'http://music.163.com/api/v1/artist/{}'


def listify(obj):
    if isinstance(obj, list):
        return obj
    else:
        return [obj]


def search_artist_blur(artist_blur, limit=1):
    """ 由于没有选择交互的过程, 因此 artist_blur 如果输入的不准确, 可能会查询到错误的歌手 """
    logging.info('开始搜索: ' + artist_blur)
    
    num = 0
    if not artist_blur:
        logging.info('Missing artist. Skipping match')
        return None

    url = COMMON_SEARCH_URL_WANGYI.format(
        urllib.parse.quote(artist_blur.lower()), 100, 0, limit)
    artists = []
    try:
        response = requests.get(url=url, headers=headers).json()
        artist_results = response['result']
        num = int(artist_results['artistCount'])
        lim = min(limit, num)
        logging.info('搜索到的歌手数量：' + str(lim))
        for i in range(lim):
            try:
                artists = listify(artist_results['artists'])
            except:
                logging.error('Error retrieving artist search results.')
    except:
        logging.error('Error retrieving artist search results.')
    if len(artists) > 0:
        return artists[0]
    return None


def search(artist_id):
    if not artist_id:
        logging.info('Missing artist. Skipping match')
        return None
    url = ARTIST_SEARCH_URL.format(artist_id)
    try:
        resp = requests.get(url=url, headers=headers).json()
        return resp
    except:
        return None


@app.route('/profile', methods=['GET'])
@v1_bp.route('/profile/advance', methods=['GET'])
@cache.cached(timeout=86400, key_prefix=make_cache_key)
def profile_json():
    match require_auth(request=request):
        case -1:
            return render_template_string(webui.error()), 403
        case -2:
            return render_template_string(webui.error()), 421
    if not bool(request.args):
        abort(404, "请携带参数访问")
    artist = unquote_plus(request.args.get('artist', ''))
    if blur_result := search_artist_blur(artist_blur=artist):
        if profile := search(blur_result['id']):
            return jsonify(profile)
    abort(400, "无法查询到歌手信息")
    