'''
based on a fork by
The_Exile (http://www.reddit.com/user/the_exiled_one/)

This script allows you to use bitvisitor.com without having to open it in a webbrowser.
However, you will still have to wait the 5 minutes and use captcha brotherhood software to
solve captchas automagically.
 
This script was tested with Python 2.7 on Windows 7. Besides the standard stuff,
it depends on BeautifulSoup (http://www.crummy.com/software/BeautifulSoup/)
and PIL (http://www.pythonware.com/products/pil/).

config.txt structure (TAB is used as separator):

Bitcoin's address	1FStudcL2ZkAweuC5F6wg6vz9sHEmg8oT3
Captcha brotherhood user	your captchabrotherhood user
Captcha brotherhood password	your captchabrotherhood Pass	
Instalation path	C:\YOURiNSTALATIONPATH\BitVisitorBot\
MInimum profit	.0
Waiting time for internet conection	60
Waiting for reach minimum profit	120
Waiting time for captchabrotherhood credits	120

usage: python BitVisitorBot.py 
 
optional arguments:
 -h, --help                      Show this help message and exit.

Created on 01.06.2014
Last update on 01.06.2014
@author: Fernando Becerra 
Feel free to drop me a coin or two at 1FStudcL2ZkAweuC5F6wg6vz9sHEmg8oT3
'''

import os, subprocess, string
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from cStringIO import StringIO
from cookielib import CookieJar
from random import randrange, choice
from time import sleep
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPCookieProcessor, install_opener, build_opener, URLError, HTTPError
from subprocess import Popen
from PIL import Image
import datetime

class readConfig:
    def __init__(self):
        fd = open('config.txt')
        count = 0
        for line in fd.readlines():
            cols = line.split('\t')
            if count == 0:
                self.addr = cols[1].rstrip('\n')
            if count == 1:
                self.cbrotherhooduser = cols[1].rstrip('\n')
            if count == 2:
                self.cbrotherhoodpass = cols[1].rstrip('\n')
            if count == 3:
                self.installedpath = cols[1].rstrip('\n')
            if count == 4:
                self.minimumprofit = float(cols[1])
            if count == 5:
                self.conntime = int(cols[1])
            if count == 6:
                self.profittime = int(cols[1])
            if count == 7:
                self.credittime = int(cols[1])
            if count > 7:
                break
            count = count + 1
        fd.close()
 
class PyVisitor:
    def __init__(self):
        self.__currentProfit = .0
        self.__currency = ''
        self.__captchaURL = None
        self.__host = 'http://bitvisitor.com/'
        defaultAgent = 'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.15'
        self.__headers = {'Accept':'text/html,application/xhtml+xml,application/xml',
                          'User-Agent':defaultAgent}
        config = readConfig()
        self.__addr = config.addr
        print self.__addr
        self.__cbrotherhooduser = config.cbrotherhooduser
        self.__cbrotherhoodpass = config.cbrotherhoodpass
        self.__conntime = config.conntime
        self.__credittime = config.credittime
        self.__profittime = config.profittime
        self.__minimumprofit = config.minimumprofit
        self.__installedpath = config.installedpath
        
        install_opener(build_opener(HTTPCookieProcessor(CookieJar())))
         
    def __getCaptchaURL(self, soup):
       captchaImg = soup.find('img', id='siimage')
       if not captchaImg:
           return False
       earning = soup.find('h1', 'page-header').contents[1].split()
       self.__currentProfit = float(earning[0])
       self.__currency = earning[1]
       self.__captchaURL = self.__host + captchaImg['src'].lstrip('./')
       return self.__captchaURL

    #FBA
    def __captcha_solver (self,image):

        image.save('temp.png')
        print 'resolver.bat ' + self.__cbrotherhooduser + ' ' + self.__cbrotherhoodpass + ' ' + self.__installedpath
        p = Popen('resolver.bat ' + self.__cbrotherhooduser + ' ' + self.__cbrotherhoodpass + ' ' + self.__installedpath )
        stdout, stderr = p.communicate()

        fderror = open( "error.txt" )
        if fderror.readline()[:10] == 'No Credits':
            return False
        else:
            fd = open( "output.txt" )
            return fd.readline()[23:]
        
 
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
        try:
            res = urlopen(req)  # set session cookie
        except URLError, e:
             print 'URL error. Will attempt again in ' + str(self.__conntime) + ' seconds'
             sleep(self.__conntime)
             self.visit()
        except HTTPError, e:
             print 'HTTP error. Will attempt again in ' + str(self.__conntime) + ' seconds'
             sleep(self.__conntime)
             self.visit()   

        if 'abuse' in res.geturl():
            print 'ERROR: The IP address was deemed suspicious.'
            return

        if 'Invalid' in res.geturl():
            print 'ERROR: Bitcoin Adress Invalid check config.txt file.'
            return

        # Please do not change the address in the next line. It costs you nothing, but it helps me.
        params = urlencode({'addr':self.__addr, 'ref':'1PZDMtiSK9yjZWEjcEeTzZLCDL92b4HXTr'})
        url = self.__host + 'next.php'
        self.__headers['Referer'] = url
        req = Request(url, params, self.__headers)
        while True:
            try:
                res = urlopen(req)
            except URLError, e:
                print 'URL error. Will attempt again in ' + str(self.__conntime) + ' seconds'
                sleep(self.__conntime)
                continue
            except HTTPError, e:
                print 'HTTP error. Will attempt again in ' + str(self.__conntime) + ' seconds'
                sleep(self.__conntime)
                continue

            if 'abuse' in res.geturl():
                print 'ERROR: The IP address was deemed suspicious.'
                break
            soup = BeautifulSoup(res.read())
            noImage = False
            if not self.__getCaptchaURL(soup): noImage = True
            a = None
            if self.__currentProfit < self.__minimumprofit:
                print str(self.__currentProfit) + self.__currency + '. Is bitvisitor fucking kidding me?!'
                res.close()
                flog = open('logvisitor.csv','a')
                flog.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+';'+'earning too low '+';'+ str(self.__currentProfit)+"\n")
                flog.close()
                sleep(self.__profittime)
                continue
            while not a:
                captcha = {}
                #InputWindow(captcha, Image.open(StringIO(urlopen(self.__captchaURL).read())), self.__currentProfit)

                if noImage : captcha[0] = '6'
                else:
                    im = Image.open(StringIO(urlopen(self.__captchaURL).read()))
                    captcha[0] = self.__captcha_solver(im)

                if not captcha.get(0):
                    print 'No Credits at CaptchaBrotherhood ...'
                    flog = open('logvisitor.csv','a')
                    flog.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+';'+'No credits' +';'+ str(self.__currentProfit)+ "\n") 
                    flog.close()
                    sleep(self.__credittime)
                    ferror = open('error.txt','w')
                    ferror.write('There are enough credits')
                    ferror.close()
                    continue
                cParams = urlencode({'ct_captcha':captcha[0], 'addr':self.__addr})
                
                try:
                    soup = BeautifulSoup(urlopen(Request(url, cParams, self.__headers)).read())
                    form = soup.find('form', action='next.php')
                    message = soup.get_text()
                                            
                    #if not form:
                    if message == 'Incorrect security code entered.Try Again.':
                        print message
                        continue
                    if captcha[0] != '6':
                        a = form.find('input', {'name':'a'})['value']
                        t = form.find('input', {'name':'t'})['value']
            
                except URLError, e:
                    print 'URL error. Will attempt again in ' + str(self.__conntime) + ' seconds'
                    sleep(self.__conntime)
                    continue
                
                if a and t:
                    break
            if not a:  # aborted by user or site error
                break
            self.__wait(soup)
            nParams = urlencode({'addr':self.__addr, 'a':a, 't':t})
            try:
                res = urlopen(Request(url, nParams, self.__headers))
            except URLError, e:
                print 'URL error. Will attempt again in ' + str(self.__conntime) + ' seconds'
                sleep(self.__conntime)
            except HTTPError, e:
                print 'HTTP error. Will attempt again in ' + str(self.__conntime) + ' seconds'
                sleep(self.__conntime)
            if not res:
                break
            print 'Earned {0:g} {1}'.format(self.__currentProfit, self.__currency)
            #time.sleep(90)
            flog = open('logvisitor.csv','a')
            flog.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+';'+'Earned '+';'+ str(self.__currentProfit)+ "\n")  
            flog.close()
                
 
def main():

    try:
        PyVisitor().visit()
    except URLError as e:
        print str(e)
 
if __name__ == "__main__":
    main()
