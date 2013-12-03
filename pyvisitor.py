'''
This script allows you to use bitvisitor.com without having to open it in a webbrowser. 
However, you will still have to wait the 5 minutes and enter the captchas manually. 
It is mainly a console application, but a small window will ask you for the captchas. 

This script was tested with Python 2.7 on Windows 7. Besides the standard stuff, 
it depends on BeautifulSoup (http://www.crummy.com/software/BeautifulSoup/) 
and PIL (http://www.pythonware.com/products/pil/). 

usage: pyvisitor.py [-h] [-u path] [-a address]        (all arguments are optional)

optional arguments:
  -h, --help                      Show this help message and exit.
  -u path, --user-agents path     A path to a file containing a user-agent on each line.
  -a address, --address address   Your bitcoin address. If omitted, you will be prompted.

Created on 02.01.2013
Last update on 30.07.2013
@author: The_Exile (http://www.reddit.com/user/the_exiled_one/)
Feel free to drop him a coin or two at 13QgXZGtXYEY9cnEB9mGuD1ZbXMWirTicg
'''

from PIL import Image, ImageTk
from Tkinter import Tk, Entry, Label
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from cStringIO import StringIO
from cookielib import CookieJar
from random import randrange, choice
from time import sleep
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPCookieProcessor, install_opener, build_opener, URLError

class InputWindow:
    def __init__(self, container, img=None, p=None):
        root = Tk()
        root.attributes('-topmost', 1)
        hint = '(Enter - submit, Esc - abort)'
        if img is None:
            root.wm_title('Address')
            hint = 'Please enter your Bitcoin address.\n' + hint
        else:
            root.wm_title('Captcha {0:g}'.format(p))
            img = ImageTk.PhotoImage(img)
            root.img_reference = img
        image = Label(root, image=img, text=hint, compound='top')
        image.pack()
        entry = Entry(root)
        entry.bind('<Escape>', lambda _:root.destroy())
        entry.bind('<Return>', lambda _:(container.setdefault(0, (entry.get())), root.destroy()))
        entry.pack()
        entry.focus_set()
        root.update_idletasks()
        xp = (root.winfo_screenwidth() / 2) - (root.winfo_width() / 2) - 8
        yp = (root.winfo_screenheight() / 2) - (root.winfo_height() / 2) - 20
        root.geometry('+%d+%d' % (xp, yp))
        root.mainloop()

class PyVisitor:
    def __init__(self, address=None, agentFile=None):
        self.__addr = address
        if not address:
            address = {}
            InputWindow(address)
            if not address.get(0):
                print 'Aborted by user.'
                exit(0)
            self.__addr = address[0]
        self.__currentProfit = .0
        self.__currency = ''
        self.__captchaURL = None
        self.__host = 'http://bitvisitor.com/'
        defaultAgent = 'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.15'
        self.__headers = {'Accept':'text/html,application/xhtml+xml,application/xml',
                          'User-Agent':defaultAgent}
        install_opener(build_opener(HTTPCookieProcessor(CookieJar())))
        if agentFile:
            try:
                with open(agentFile) as f:
                    self.__headers['User-Agent'] = choice([agent.rstrip() for agent in f])
            except:
                print 'Using default User-Agent.'
            print 'User-Agent:', self.__headers['User-Agent']
        print 'Bitcoin address:', self.__addr

    def __getCaptchaURL(self, soup):
        captchaImg = soup.find('img', id='siimage')
        if not captchaImg:
            return
        earning = soup.find('h1', 'page-header').contents[1].split()
        self.__currentProfit = float(earning[0])
        self.__currency = earning[1]
        self.__captchaURL = self.__host + captchaImg['src'].lstrip('./')
        return self.__captchaURL

    def __wait(self, soup):
        siteFrame = soup.find('iframe', id='mlsFrame')
        if not siteFrame: return
        print 'Visiting', siteFrame['src']
        print 'Getting {0:g} {1} in'.format(self.__currentProfit, self.__currency),
        for i in range(5, 0, -1):
            print i,
            sleep(60)
        print
        sleep(randrange(1, 10))  # just to be sure ;)

    def visit(self):
        req = Request(self.__host, None, self.__headers)
        res = urlopen(req)  # set session cookie
        if 'abuse' in res.geturl():
            print 'ERROR: The IP address was deemed suspicious.'
            return
        # The following address stands for a referral link. Right now it points to my address.
        # Feel free to change it to whatever you like when you redistribute the source code.
        # FYI, the original author's address is 13QgXZGtXYEY9cnEB9mGuD1ZbXMWirTicg.
        # Make sure to thank him with a small donation.
        params = urlencode({'addr':self.__addr, 'ref':'14g89sH9GV2RLR8hSh7cYqSKm4ephPbdKz'})
        url = self.__host + 'next.php'
        self.__headers['Referer'] = url
        req = Request(url, params, self.__headers)
        while True:
            res = urlopen(req)
            if 'abuse' in res.geturl():
                print 'ERROR: The IP address was deemed suspicious.'
                break
            soup = BeautifulSoup(res.read())
            if not self.__getCaptchaURL(soup): break
            a = None
            while not a:
                captcha = {}
		InputWindow(captcha, Image.open(StringIO(urlopen(self.__captchaURL).read())), self.__currentProfit)
                if not captcha.get(0):
                    print 'Aborted by user.'
                    break
                cParams = urlencode({'ct_captcha':captcha[0], 'addr':self.__addr})
                soup = BeautifulSoup(urlopen(Request(url, cParams, self.__headers)).read())
                form = soup.find('form', action='next.php')
                if not form:
                    message = soup.get_text()
                    if 'Incorrect' in message: continue
                    print message
                    break
                a = form.find('input', {'name':'a'})['value']
                t = form.find('input', {'name':'t'})['value']
                if a and t:
                    break
            if not a:  # aborted by user or site error
                break
            self.__wait(soup)
            nParams = urlencode({'addr':self.__addr, 'a':a, 't':t})
            res = urlopen(Request(url, nParams, self.__headers))
            if not res:
                break
            print 'Earned {0:g} {1}'.format(self.__currentProfit, self.__currency)

def main():
    parser = ArgumentParser()
    parser.add_argument('-u', '--user-agents', metavar='path',
                        help='A path to a file containing a user-agent on each line.')
    parser.add_argument('-a', '--address', metavar='address',
                        help='Your bitcoin address. If omitted, you will be prompted.')
    ns = parser.parse_args()
    try:
        PyVisitor(ns.address, ns.user_agents).visit()
    except URLError as e:
        print str(e)

if __name__ == "__main__":
    main()
