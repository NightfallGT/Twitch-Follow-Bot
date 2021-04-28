import requests
import logging
import json
from colorama import Fore, Style, init 
import os
import platform
from typing import List

init(convert=True)

logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S', level=logging.INFO) #change to logging.DEBUG

def clear():
    system = platform.system()
    if system == 'Windows':
        os.system('cls')
    elif system == 'Linux':
        os.system('clear')
    else:
        print('\n')*120

class Twitch:
    def __init__(self):
        self.HEADERS = {
            "content-type": "application/json",
            "accept" : "application/json",
            "api-consumer-type":  "mobile; iOS/203500927335335108",
            "accept-charset": "utf-8",
            "client-id":  "85lcqzxpb9bqu9z6ga1ol55du",
            "accept-language": "en-us",
            "accept-encoding": "br, gzip, deflate",
            "user-agent": "Twitch 203500927335335108 (iPhone; iOS 12.3.1; en_US)",
            "x-apple-model":  "iPhone 7",
            "x-app-version":  "9.10.1",
            "x-apple-os-version": "12.3.1"
        }

    def _read_file(self, file:str) -> List[str]:
        with open(file, 'r', encoding='utf-8') as f:
            contents = [line.strip('\n') for line in f]
        return contents

    def _update_header(self, oauth: str) -> None:
        self.HEADERS['Authorization'] = 'OAuth ' + oauth

    def _login(self, username: str, password: str) -> bool:
        data = {
        'username': username,
        'password': password,
        'client_id': '85lcqzxpb9bqu9z6ga1ol55du'
        }

        r = requests.post('https://passport.twitch.tv/login', json=data)
        logging.debug(r.text)

        if 'access_token' in r.text:
            token = r.json()['access_token']
            logging.debug('Login succeded')
            logging.debug('Token:%s' %token)
            return token

        if 'captcha' in r.text:
            logging.warning('Captcha is required..')
        
        logging.debug(r.text)
        return False 

    def _get_cid(self, user: str, token: str) -> str:
        cl= 'https://api.twitch.tv/api/channels/' + user + '/access_token?need_https=true&oauth_token=' + token
        logging.debug('Channel post link for _cid created: %s' % cl)   

        channel = requests.get(cl, headers=self.HEADERS)

        logging.debug(channel.text)

        try:
            token_info = channel.json()['token'] 
            channel_id = json.loads(token_info)['channel_id']
            logging.debug(channel_id)
            return channel_id    
        except KeyError:
            return False

    def _follow(self, channel_id: str) -> bool:
        payload = '[{\"operationName\":\"FollowButton_FollowUser\",\"variables\":{\"input\":{\"disableNotifications\":false,\"targetID\":\"%s\"}},\"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"51956f0c469f54e60211ea4e6a34b597d45c1c37b9664d4b62096a1ac03be9e6\"}}}]' % channel_id

        r = requests.post('https://gql.twitch.tv/gql', data=payload, headers=self.HEADERS)

        if 'error' in r.text:
            logging.error('Error in following user.')
            logging.error(r.text)
        
        else:
            try:
                followed_user = r.json()[0]['data']['followUser']['follow']['user']
                logging.debug('Success!')
                logging.info('Followed %s ID: %s' % (followed_user['displayName'], followed_user['id']))
                return True
            except Exception as e:
                logging.error('Error in following user.')
                logging.warning(e)

        return False

    def _unfollow(self, channel_id:str) -> bool:
        payload = '[{"operationName":"FollowButton_UnfollowUser","variables":{"input":{"targetID":"%s"}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"d7fbdb4e9780dcdc0cc1618ec783309471cd05a59584fc3c56ea1c52bb632d41"}}}]' % channel_id

        r = requests.post('https://gql.twitch.tv/gql', data=payload, headers=self.HEADERS)

        if 'error' in r.text:
            logging.error('Error in unfollowing user.')
            logging.error(r.text)

        else:
            try:
                reqid = r.json()[0]['extensions']['requestID']
                logging.info('Unfollowed user [requestID: %s]'% reqid )
                return True
            except Exception as e:
                logging.error('Error in unfollowing user.')
                logging.warning(e)

        return False
class Converter(Twitch):
    def __init__(self):
        super().__init__()
        self.combo_list = self._read_file('config/convert.txt')

    def _write_token(self, content: str) -> None:
        with open('output/oauth_tokens.txt', 'a', encoding='utf-8') as f:
            f.write('%s\n' % content)

    def convert(self):
        for x in self.combo_list:
            combo = x.split(':')
            token = self._login(combo[0], combo[1])
            if token:
                logging.info('Successfully converted [%s] to [%s]' % (x, token))
                self._write_token(token)

            else:
                logging.info('Unable to convert [%s]' % x )

class Follow(Twitch):
    def __init__(self, channel: str):
        super().__init__()
        self.token_list = self._read_file('config/oauth_tokens.txt')
        self.channel = channel
        self.channel_id = self._cid()

    def _cid(self):
        access = 'qecxhnjevnnfvskhhd07od91yliqti'
        self._update_header(access)
        channel_id = self._get_cid(self.channel, access)
        return channel_id

    def follow(self):
        count = 0
        failed = 0
        if self.channel_id:
            for token in self.token_list:
                logging.debug('Current token: %s' % token)
                self._update_header(token)
                logging.debug('Added Authorization oAuth to header')
                followed = self._follow(self.channel_id)

                if followed:
                    count += 1
                else:
                    failed += 1

                os.system('title Twitch Follow Bot ^| Followers Sent: %d ^| Failed: %d' % (count, failed))
        else:
            logging.warning('Channel ID is null')

    def unfollow(self):
        count = 0
        failed = 0
        if self.channel_id:
            for token in self.token_list:
                logging.debug('Current token: %s' % token)
                self._update_header(token)
                unfollowed = self._unfollow(self.channel_id)

                if unfollowed:
                    count += 1
                else:
                    failed += 1

                os.system('title Twitch Unfollow Bot ^| Success Count: %d ^| Failed: %d' % (count, failed))

        else:
            logging.warning('Channel ID is null')
def title():
    title= f'''{Fore.LIGHTRED_EX}
\t\t▄▄▄▄▄▄▄▌ ▐ ▄▌▪  ▄▄▄▄▄ ▄▄·  ▄ .▄  ·▄▄▄      ▄▄▌  ▄▄▌        ▄▄▌ ▐ ▄▌  ▄▄▄▄·       ▄▄▄▄▄
\t\t•██  ██· █▌▐███ •██  ▐█ ▌▪██▪▐█  ▐▄▄  ▄█▀▄ ██•  ██•   ▄█▀▄ ██· █▌▐█  ▐█ ▀█▪ ▄█▀▄ •██  
\t\t ▐█.▪██▪▐█▐▐▌▐█· ▐█.▪██ ▄▄██▀▀█  █  ▪▐█▌.▐▌██ ▪ ██ ▪ ▐█▌.▐▌██▪▐█▐▐▌  ▐█▀▀█▄▐█▌.▐▌ ▐█.▪
\t\t ▐█▌·▐█▌██▐█▌▐█▌ ▐█▌·▐███▌██▌▐▀  ██ .▐█▌.▐▌▐█▌ ▄▐█▌ ▄▐█▌.▐▌▐█▌██▐█▌  ██▄▪▐█▐█▌.▐▌ ▐█▌·
\t\t ▀▀▀  ▀▀▀▀ ▀▪▀▀▀ ▀▀▀ ·▀▀▀ ▀▀▀ ·  ▀▀▀  ▀█▄▀▪.▀▀▀ .▀▀▀  ▀█▄▀▪ ▀▀▀▀ ▀▪  ·▀▀▀▀  ▀█▄▀▪ ▀▀▀ {Style.RESET_ALL}
        '''
    return title


def menu():
    menu = f'''{Fore.LIGHTRED_EX}
                                         ╔══════════════════════════════╗
                                                  [1] Follow Bot
                                                  [2] Unfollower
                                                  [3] Converter
                                         ╚══════════════════════════════╝    {Style.RESET_ALL}
        '''
    return menu

def logic():
    user_choice = int(input(f'{Fore.LIGHTRED_EX}\t[?] > {Style.RESET_ALL}'))

    if user_choice == 1:
        clear()
        print(title())
        print('\n\n\n')
        channel = input('Enter name of channel to follow [e.g Ninja]: ')
        Follow(channel).follow()

    elif user_choice == 2:
        clear()
        print(title())
        print('\n\n\n')
        channel = input('Enter name of channel to unfollow: ')
        Follow(channel).unfollow()

    elif user_choice == 3:
        clear()
        print(title())
        print('\n\n\n\n')
        print('Converting username:password to token from config/convert.txt')
        Converter().convert()

    else:
        print('Invalid Choice')

def main():
    os.system('title [Twitch Follow Bot] ^| NightfallGT')
    clear()
    print(title())
    print(menu())
    print('\n')
    logic()
    
if __name__ == '__main__':
    main()
