import json
import os
from log import logging
from request import req
from discord_webhook import DiscordWebhook, DiscordEmbed


if __name__ != "__main__":
    raise Exception('Run hoyolab.py as main')

logging.info('Hoyolab Auto Daily Check-in Starting ...')

cookie = os.environ.get('COOKIE', '')
logging.info('Reading Hoyolab cookie from environment variable ..');

if (cookie == ''):
    logging.error("Variable 'COOKIE' not found, please ensure that variable exists")
    exit(1)
else: 
    logging.info("Variable 'COOKIE' found, verifiying cookie ...")

header = {
    'User-Agent': os.environ.get(
        'USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47'
    ),
    'Referer': 'https://act.hoyolab.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cookie': cookie
}

res = req.to_python(req.request(
    'get',
    'https://api-account-os.hoyolab.com/auth/api/getUserAccountInfoByLToken',
    headers=header
).text)

if (res.get('retcode', 0) != 0):
    logging.error("Variable 'COOKIE' not valid, please ensure that value is valid")
    exit(1)

logging.info('Scanning for hoyoverse game account')
res = req.to_python(req.request(
    'get',
    'https://api-os-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie',
    headers=header
).text)

all_game_biz = []
for list in res.get('data', {}).get('list', []):
    game_biz = list.get('game_biz', '')
    if game_biz not in all_game_biz:
        all_game_biz.append(game_biz)
for biz in all_game_biz:
    index = 0
    res = req.to_python(req.request(
        'get',
        'https://api-os-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz={}'.format(biz),
        headers=header
    ).text)

    account_list = res.get('data', {}).get('list', [])

    if len(account_list) != 1:
        highest_level = account_list[0].get('level', 'NA')

    for i in range(1, len(account_list)):
        if account_list[i].get('level', 'NA') > highest_level:
            highest_level = account_list[i].get('level', 'NA')
            index = i
    
    region_name = account_list[index].get('region_name', '')
    uid = account_list[index].get('game_uid', '')
    level = account_list[index].get('level', '')
    nickname = account_list[index].get('nickname', '')
    region = account_list[index].get('region', '')

    if account_list[index].get('game_biz', '') == 'hk4e_global':
        logging.info('Genshin Impact Account found in server {}'.format(region_name))
        act_id = 'e202102251931481'
        info_url = 'https://hk4e-api-os.mihoyo.com/event/sol/info?act_id={}'.format(act_id) 
        reward_url = 'https://hk4e-api-os.mihoyo.com/event/sol/home?act_id={}'.format(act_id)
        sign_url = 'https://hk4e-api-os.mihoyo.com/event/sol/sign?act_id={}'.format(act_id)
        suffix = 'Traveller'
        title = 'Genshin Impact Daily Login'
        color = 'E86D82'
        author_name = 'Paimon'
        author_url = 'https://genshin.hoyoverse.com'
        author_icon = 'https://img-os-static.hoyolab.com/communityWeb/upload/1d7dd8f33c5ccdfdeac86e1e86ddd652.png'
    elif account_list[index].get('game_biz', '') == 'bh3_global':
        logging.info('Honkai Impact 3 Account found in server {}'.format(region_name))
        act_id = 'e202110291205111'
        info_url = 'https://sg-public-api.hoyolab.com/event/mani/info?act_id={}'.format(act_id) 
        reward_url = 'https://sg-public-api.hoyolab.com/event/mani/home?act_id={}'.format(act_id)
        sign_url = 'https://sg-public-api.hoyolab.com/event/mani/sign?act_id={}'.format(act_id)
        suffix = 'Captain'
        title = 'Honkai Impact 3rd Daily Login'
        color = 'A385DE'
        author_name = 'Ai-chan'
        author_url = 'https://honkaiimpact3.hoyoverse.com/global/en-us'
        author_icon = 'https://img-os-static.hoyolab.com/communityWeb/upload/bbb364aaa7d51d168c96aaa6a1939cba.png'
    else:
        logging.error('Genshin Or Honkai Account not found !')
        exit(1)

    logging.info('Checking in UID {} ...'.format(uid))

    logging.info('Fetch account detail from hoyoverse ...')
    res = req.to_python(
        req.request('get', info_url, headers=header).text
    )
    
    login_info = res.get('data', {})
    today = login_info.get('today')
    total_sign_day = login_info.get('total_sign_day')

    logging.info('Fetch daily login reward from hoyoverse ..')
    res = req.to_python(
        req.request('get', reward_url, headers=header).text
    )
    reward = res.get('data', {}).get('awards')

    message_list = []

    if login_info.get('is_sign') is True:
        award_name = reward[total_sign_day - 1]['name']
        award_cnt = reward[total_sign_day - 1]['cnt']
        award_icon = reward[total_sign_day - 1]['icon']
        status = "{}, you've already checked in today".format(suffix)
        logging.info("{}, you've already checked in today".format(suffix))
    else:
        award_name = reward[total_sign_day]['name']
        award_cnt = reward[total_sign_day]['cnt']
        award_icon = reward[total_sign_day]['icon']

        logging.info("Sign-in to server and claim reward.")
        try:
            res = req.to_python(req.request(
                'post', sign_url, headers=header,
                data=json.dumps({
                'act_id': act_id
            }, ensure_ascii=False)).text)
        except Exception as e:
            raise Exception(e)
        code = res.get('retcode', 99999)
        if code == 0:
            status = 'Sucessfully claim daily reward'
            total_sign_day = total_sign_day + 1
            logging.info('Sucessfully claim daily reward')
        else:
            status = 'Something went wrong.\n {}'.format(res.get('message', ''))
            logging.info(status)

    if login_info.get('first_bind') is True:
        status = f'Please check in manually once'
        award_name = '-'
        award_cnt = '-'
        award_icon = ''
        total_sign_day = 0
        logging.info('Please check in manually once')

    webhook = os.environ.get('DISCORD_WEBHOOK','')
    if (webhook != ''):
        webhook = DiscordWebhook(url=webhook)
        embed = DiscordEmbed(title=title, description=status, color=color)
        embed.set_thumbnail(url=award_icon)
        embed.set_author(
            name=author_name,
            url=author_url,
            icon_url=author_icon,
        )
        embed.set_footer(text='Hoyolab Auto Login', icon_url='https://img-os-static.hoyolab.com/favicon.ico')
        embed.set_timestamp()
        embed.add_embed_field(name="Nickname", value=nickname)
        embed.add_embed_field(name="UID", value=uid)
        embed.add_embed_field(name="Level", value=level)
        embed.add_embed_field(name="Server", value=f'{region_name}')
        embed.add_embed_field(name="Today's rewards", value=f'{award_name} x {award_cnt}')
        embed.add_embed_field(name="Total Daily Check-In", value=total_sign_day)
        embed.add_embed_field(name="Check-in result:", value=status, inline=False)
        webhook.add_embed(embed)
        response = webhook.execute()
        if (response.status_code == 200):
            logging.info(f'Successfully send notification to your own discord')
        else:
            logging.error(f'Discord FAILED\n{response}')

logging.info('Script Ended')
exit(1)
