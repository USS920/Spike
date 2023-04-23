import os
import time
import datetime
import requests
from datetime import datetime as dt, timedelta
import logging
from symbology import *
import pyotp
import sys
sys.path.append("/home/ec2-user/newalgo/trades/"+dt.now().strftime("%d-%m-%y"))
from firestraddle import *

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

#This is spike alert channel.
def tg_alert(bot_message):
    try:
        bot_token = "5815892603:AAH8wveicjUYNQE"
        bot_chatID = "-100176599"
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
    except:
        pass

def tg_st(bot_message):
    try:
        bot_token = "5815892603:AAH8wLQUYNQPw3E"
        bot_chatID = "-109695"
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
    except:
        pass
def tg_log_sos(bot_message):
    try:
        bot_token = "5588744140:AATHmC3I-Z3kZk"
        bot_chatID = "-100155"
        send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
    except:
        pass

def read_lot_size():
    global nf_lot_size
    global bn_lot_size
    global funds_alert
    with open('lot_size_b.json', 'r') as lsf:
        user_param = json.load(lsf)
    return user_param['nf_lot_size'], user_param['bn_lot_size'], user_param['funds_alert']


def read_creds():
    try:
        with open('credentials.json', 'r') as f:
            cred_dict = json.load(f)
            return cred_dict
    except Exception as e:
        print("Reading User Credentials Failed with Error : ", e)
        tg_log_sos("Reading User Credentials Failed with Error : " + str(e))


def login(obj, cred_dict):
    ret = None
    try:
        with open("user_obj.txt", 'r') as uo:
            ut = uo.readline()
        ss = obj.set_session(userid=cred_dict['username'],
                             password=cred_dict['pwd'],
                             usertoken=ut)
        if (obj.get_limits()['stat'] == 'Not_Ok'):
            ret = obj.login(userid=cred_dict['username'],
                            password=cred_dict['pwd'],
                            twoFA=str(pyotp.TOTP(cred_dict['factor2']).now()),
                            vendor_code=cred_dict['vc'],
                            api_secret=cred_dict['app_key'],
                            imei=cred_dict['imei'])
            print(ret)
            if ret != None:
                login_status = ret['stat']

                if login_status == 'Ok':
                    login_time = ret['request_time']
                    login_user_name = ret['uname']
                    login_usertoken = ret['susertoken']
                    with open("user_obj.txt", 'w') as f:
                        f.write(login_usertoken)
                    return ret

    except Exception as e:
        print("User Login Request Failed with Error : ", e)
        tg_log_sos("User Login Request Failed with Error : " + str(e))


def create_shoonya_obj():
    host = 'https://api.shoonya.com/NorenWClientTP/'
    websocket = 'wss://api.shoonya.com/NorenWSTP/'
    eodhost = 'https://shoonya.finvasia.com/chartApi/getdata/'

    try:
        obj = NorenApi(host, websocket, eodhost)
        return obj
    except Exception as e:
        print("Shoonya Object Creation Failed with Error : ", e)
        tg_log_sos("Shoonya Object Creation Failed with Error : " + str(e))


def find_scrip_details(symbol, type, req_field, opt_expiry=None, opt_type=None, opt_strike=None):
    if type == 'INDEX':
        if symbol in ['NIFTY50', 'NIFTY 50', 'NIFTY']:
            symbol = 'Nifty 50'
        elif symbol in ['NIFTY BANK', 'BANK NIFTY', 'BANKNIFTY', 'NIFTYBANK']:
            symbol = 'Nifty Bank'
        elif symbol in ['INDIAVIX', 'INDIA VIX', 'VIX INDIA', 'VIXINDIA']:
            symbol = 'INDIAVIX'
        elif symbol in ['FINNIFTY', 'NIFTY FIN SERVICES']:
            symbol = "Nifty Fin Services"
        with open('NSE_symbols.txt', 'r') as f:
            for i in (f.readlines()):
                if symbol in i:
                    sym_exch = (i.replace('\n', '').split(','))[0]
                    sym_token = (i.replace('\n', '').split(','))[1]
                    sym_lotsize = (i.replace('\n', '').split(','))[2]
                    sym_tradingsym = (i.replace('\n', '').split(','))[4]
                    if req_field == 'token':
                        return sym_token

    elif type == 'OPTIDX':
        if symbol.isalnum():
            shoonya_symbology = symbol
        else:
            if "FIN" in symbol:
                shoonya_symbology = symbol.upper() + str(get_fn_current_expiry_date().strftime('%d%b%y')).upper() + \
                                    str(opt_type)[0].upper() + str(int(float(opt_strike)))
            else:
                shoonya_symbology = symbol.upper() + str(get_current_expiry_date().strftime('%d%b%y')).upper() + \
                                    str(opt_type)[0].upper() + str(int(float(opt_strike)))
        # print(shoonya_symbology)
        with open('NFO_symbols.txt', 'r') as f:
            for i in (f.readlines()):
                if shoonya_symbology in i:
                    sym_token = ((i.replace('\n', '')).split(','))[1]
                    sym_lotsize = ((i.replace('\n', '')).split(','))[2]
                    sym_tick_size = ((i.replace('\n', '')).split(','))[9]
                    if req_field == 'token':
                        return sym_token
                    elif req_field == 'lot_size':
                        return sym_lotsize
                    elif req_field == 'tick_size':
                        return sym_tick_size
    else:
        if type == 'INDEX':
            print("No match found for the supplied scrip : ", str(symbol) + str(type))
        elif type == 'OPTIDX':
            print("No match found for the supplied scrip : ",
                  (symbol + str(opt_expiry) + str(opt_type)[0] + str(opt_strike)))

def get_quote(obj, exch, token, req_field):
    ret = []
    try:
        ret = obj.get_quotes(exchange=exch, token=token)
        # print(ret)
        if ret['stat'] == 'Ok':
            if req_field == 'ltp':
                return float(ret['lp'])

        elif ret['stat'] == 'Not_Ok':
            print("Fetched LTP with status Not_Ok : ", ret['emsg'])
    except Exception as e:
        print("Fetching LTP failed with error : ", e)
        tg_log_sos("Fetching LTP failed with error : " + str(e))


def get_current_expiry_date():
    today_date = dt.now().date()
    expiry_days_list = []

    with open('/home/ec2-user/newalgo/core_scripts/expiry_dates.txt', 'r') as f:
        expiry_days_list = ([dt.strptime(i.replace('\n', ''), '%Y-%m-%d').date() for i in f.readlines()])

    expiry_days_list = sorted(expiry_days_list)
    for i in expiry_days_list:
        if (i - today_date) >= timedelta(0):
            return i

def get_fn_current_expiry_date():
    today_date = dt.now().date()
    expiry_days_list = []

    with open('/home/ec2-user/newalgo/core_scripts/fn_expiry_dates.txt', 'r') as f:
        expiry_days_list = ([dt.strptime(i.replace('\n', ''), '%Y-%m-%d').date() for i in f.readlines()])

    expiry_days_list = sorted(expiry_days_list)
    for i in expiry_days_list:
        if (i - today_date) >= timedelta(0):
            return i

def build_shoonya_opt_symbol(symbol, opt_type, opt_strike):
    if symbol == "FINNIFTY":
        shoonya_symbol = str(symbol.upper()) + str(get_fn_current_expiry_date().strftime('%d%b%y')).upper() + (
    str(opt_type.upper())[0]) + str(int(float(opt_strike)))
    else:
        shoonya_symbol = str(symbol.upper()) + str(get_current_expiry_date().strftime('%d%b%y')).upper() + (
    str(opt_type.upper())[0]) + str(int(float(opt_strike)))
    return shoonya_symbol

def myround(x, base):
    return int(base * round(float(x) / base))

def writefile(name, value):
    with open(name+'.txt','w') as f:
        f.write(str(value))

def readfile(name):
    with open(name+'.txt','r') as f:
        val = float(f.readline())
        return val

nfs = setup_logger('nfs', '/home/ec2-user/newalgo/personal/nf.log')
bns = setup_logger('bns', '/home/ec2-user/newalgo/personal/bn.log')
ffs = setup_logger('ffs', '/home/ec2-user/newalgo/personal/fn.log')


#Restore it to 9
if dt.now().hour <= 9 and dt.now().minute <= 18:
    with open('/home/ec2-user/newalgo/personal/nf.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/bn.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/fn.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/st_nf.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/st_bn.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/st_fn.log', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/minprembf.txt', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/minpremnf.txt', 'w') as f:
        f.write('')
    with open('/home/ec2-user/newalgo/personal/minpremfn.txt', 'w') as f:
        f.write('')

readfile("NBNA")
readfile("NBNB")
readfile("NBNC")
readfile("NIFA")
readfile("NIFB")
readfile("NIFC")
readfile("FINA")
readfile("FINB")
readfile("FINC")
readfile("GUTA")
readfile("GUTB")
readfile("GUTC")
def opt():
    user_dict = read_creds()
    nf_lot_size, bn_lot_size, funds_alert = read_lot_size()
    #
    user_obj = create_shoonya_obj()
    user_login = login(user_obj, user_dict)
    bstprmin = 100000
    nstprmin = 100000
    fstprmin = 100000
    
    bstprmax = 0
    nstprmax = 0
    fstprmax = 0
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    percentages = [
        [12, 18, 20, 14, 20, 25],
        [14, 20, 25, 16, 22, 30],
        [25, 50, 100, 30, 55, 110],
        [30, 60, 100, 30, 70, 120],
        [12, 18, 20, 14, 20, 25],
        [12, 18, 20, 14, 20, 25],
        [12, 18, 20, 14, 20, 25]
    ]
    p1, p2, p3, p4, p5, p6 = [p/100+1 for p in percentages[today]]
    #p1 p2 p3 are the stop losses for the theta strategies, p4 p5 p6 are for delta strategies.
    percentages_fin = [
        [25, 50, 80, 30, 55, 85],
        [30, 60, 100, 30, 70, 120],
        [12, 18, 20, 14, 20, 25],
        [12, 18, 20, 14, 20, 25],
        [14, 20, 25, 16, 22, 30],        
        [12, 18, 20, 14, 20, 25],
        [12, 18, 20, 14, 20, 25]
    ]
    pf1, pf2, pf3, pf4, pf5, pf6 = [p/100+1 for p in percentages_fin[today]]
    sl=[
        ["07","08","09"],
        ["07","08","09"],
        ["07","08","09"],
        ["07","08","09"],
        ["07","08","09"],
        ["07","08","09"],
        ["07","08","09"]
    ]
    today = dt.today().weekday()
    sl1, sl2, sl3 = [p for p in sl[today]]

    sln=[
        ["04","05","06"],
        ["04","05","06"],
        ["04","05","06"],
        ["04","05","06"],
        ["04","05","06"],
        ["04","05","06"],
        ["04","05","06"]
    ]
    sln1, sln2, sln3 = [p for p in sln[today]]
    
    #Straddle in service status
    nf1status = nf2status = nf3status = bf1status = bf2status = bf3status =  fn1status = fn2status = fn3status = bf1statusg = bf2statusg = bf3statusg =0
    #Fetch the min straddle premium if day
    time_obj = datetime.datetime.strptime(time_str, '%H:%M')
    time_formatted = time_obj.strftime('%H:%M')
    if time_formatted > '09:30':
    while True:
        try:
            if dt.strptime(dt.now().strftime('%H:%M'), '%H:%M') > dt.strptime('09:25', '%H:%M'):
                with open('/home/ec2-user/newalgo/personal/minprembf.txt', 'r') as f:
                    bstprmin = float(f.readline())
                with open('/home/ec2-user/newalgo/personal/minpremnf.txt', 'r') as f:
                    nstprmin = float(f.readline())
                with open('/home/ec2-user/newalgo/personal/minpremfn.txt', 'r') as f:
                    fstprmin = float(f.readline())
                tg_log_sos("Minimum straddle Value fetched \nBN: "+str(round(bstprmin,2))+"\nNF: "+str(round(nstprmin,2))+"\nFN: "+str(round(fstprmin,2)))
                break
            else:
                break
        except:
            break
    #Counter for tg message
    num1 = num2 = num3 = num4 = num5 = num6 = num7 = num8 = num9 = numg1 = numg2 = numg3 =100
    #Counter for trigger, i.e. if this += 5 then, spike is registered.
    count1 = count2 = count3 = count4 = count5 = count6 = count7 = count8 = count9 = countg1 = countg2 = countg3 = 0

    #Trail mechanism, not implemented yet
    trailslbn = trailslnf = trailslfn=0

    while True:
        bstpr1 = bstpr2 = bstpr3 = bstpr4 = bstpr5 = nstpr1 = nstpr2 = nstpr3 = nstpr4 = nstpr5 = fstpr1 = fstpr2 = fstpr3 = fstpr4 = fstpr5 = 0
        #Setting all the variables to 0, with every iteration.

        nfatmstrike = myround(float(get_quote(user_obj, 'NSE', find_scrip_details("NIFTY", 'INDEX', 'token'), 'ltp')), 50)
        bnatmstrike = myround(float(get_quote(user_obj, 'NSE', find_scrip_details("BANKNIFTY", 'INDEX', 'token'), 'ltp')), 100)
        fnatmstrike = myround(float(get_quote(user_obj, 'NSE', find_scrip_details("FINNIFTY", 'INDEX', 'token'), 'ltp')), 50)
        
        noc = user_obj.get_option_chain("NFO", build_shoonya_opt_symbol("NIFTY", "CE", nfatmstrike), float(nfatmstrike), 2)
        boc = user_obj.get_option_chain("NFO", build_shoonya_opt_symbol("BANKNIFTY", "CE", bnatmstrike), float(bnatmstrike), 2)
        foc = user_obj.get_option_chain("NFO", build_shoonya_opt_symbol("FINNIFTY", "CE", fnatmstrike), float(fnatmstrike), 2)
        
        for scrip in boc['values']:
            if int(float(scrip["strprc"])) == int(float(bnatmstrike)):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                bstpr1=float(scripdata['lp'])+bstpr1
            if int(float(scrip["strprc"])) == int(float(bnatmstrike)-100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                bstpr2=float(scripdata['lp'])+bstpr2
            if int(float(scrip["strprc"])) == int(float(bnatmstrike)+100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                bstpr3=float(scripdata['lp'])+bstpr3
            if int(float(scrip["strprc"])) == int(float(bnatmstrike)-200):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                bstpr4=float(scripdata['lp'])+bstpr4
            if int(float(scrip["strprc"])) == int(float(bnatmstrike)+200):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                bstpr5=float(scripdata['lp'])+bstpr5
        
        values = [bstpr1, bstpr2, bstpr3, bstpr4, bstpr5]
        values.sort()
        non_zero_values = [v for v in values if v != 0]
        bstpr = min(non_zero_values)

        if bstpr>0:
            bstprmin = min(bstpr,bstprmin)
        else:
            bstprmin = 100000

        if bstprmin<=0:
            bstprmin = 100000

        bns.info(bstpr)

        if bstpr > bstprmin*p1 and bstprmin > 0 and nstprmin > 0 and bf1status == 0 and bstpr > 120 and readfile("NBNA") == 0:
            count1 += 1
            if count1 == 4:
                bf1status = 1
                count1 = 0
                num1 = 0
        else:
            count1 = 0

        if bstpr > bstprmin*p2 and bstprmin > 0 and nstprmin > 0 and bf2status == 0 and bstpr > 120 and readfile("NBNB") == 0:
            count2 += 1
            if count2 == 4:
                bf2status = 1
                num1 = 100
                num2 = 0
                count2 = 0
        else:
            count2 = 0

        if bstpr > bstprmin*p3 and bstprmin > 0 and nstprmin > 0 and bf3status == 0 and bstpr > 120 and readfile("NBNC") == 0:
            count3 += 1
            if count3 == 4:
                bf3status = 1
                num1 = 100
                num2 = 100
                num3 = 0
                count3 = 0
        else:
            count3 = 0

        if bstpr < bstprmin*p1*0.97 and bstprmin>0 and nstprmin>0 and bf1status ==1 and bstpr > 120 and readfile("NBNA") == 0:
            bf1status = 100
            tg_log_sos("Straddle NBN-A fired with SL "+str(float(sl1)/10)+"%")
            tg_alert("Selling "+str(round((p1-1)*100,0))+"% Spike BankNifty Straddle now to capture spike.")
            writefile("NBNA","1")
            fire("NBN","A",sl1)
            fire("NBN","A",sl1)
            fire("NBN","A",sl1)
        if bstpr < bstprmin*p2*0.97 and bstprmin>0 and nstprmin>0 and bf2status ==1 and bstpr > 120 and readfile("NBNB") == 0:
            bf2status = 100
            tg_log_sos("Straddle NBN-B fired with SL "+str(float(sl2)/10)+"%")
            tg_alert("Selling "+str(round((p2-1)*100,0))+"% Spike BankNifty Straddle now to capture spike.")
            writefile("NBNB","1")
            fire("NBN","B",sl2)
            fire("NBN","B",sl2)
            fire("NBN","B",sl2)
        if bstpr < bstprmin*p3*0.97 and bstprmin>0 and nstprmin>0 and bf3status ==1 and bstpr > 120 and readfile("NBNC") == 0:
            bf3status = 100 
            tg_log_sos("Straddle NBN-C fired with SL "+str(float(sl3)/10)+"%")
            tg_alert("Selling "+str(round((p3-1)*100,0))+"% Spike BankNifty Straddle now to capture spike.")
            writefile("NBNC","1")
            fire("NBN","C",sl3)
            fire("NBN","C",sl3)
            fire("NBN","C",sl3)

        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf1status ==100 and bstpr > 10 and readfile("NBNA") == 1:
#            stop("NBN","A",sl1)
            tg_log_sos("Straddle NBN-A exited with SL "+str(float(sl1)/10)+"%")
            writefile("NBNA","100")
        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf2status ==100 and bstpr > 10 and readfile("NBNB") == 1:
#            stop("NBN","B",sl2)
            tg_log_sos("Straddle NBN-B exited with SL "+str(float(sl1)/10)+"%")
            writefile("NBNB","100")
        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf3status ==100 and bstpr > 10 and readfile("NBNC") == 1:
#            stop("NBN","C",sl3)
            tg_log_sos("Straddle NBN-C exited with SL "+str(float(sl1)/10)+"%")
            writefile("NBNC","100")

        #______________________GUT___________________________
        if bstpr > bstprmin*p4 and bstprmin > 0 and nstprmin > 0 and bf1statusg == 0 and bstpr > 120 and readfile("GUTA") == 0:
            countg1 += 1
            if countg1 == 4:
                bf1statusg = 1
                countg1 = 0
                numg1 = 0
        else:
            countg1 = 0

        if bstpr > bstprmin*p5 and bstprmin > 0 and nstprmin > 0 and bf2statusg == 0 and bstpr > 120 and readfile("GUTB") == 0:
            countg2 += 1
            if countg2 == 4:
                bf2statusg = 1
                numg1 = 100
                numg2 = 0
                countg2 = 0
        else:
            count2 = 0

        if bstpr > bstprmin*p6 and bstprmin > 0 and nstprmin > 0 and bf3statusg == 0 and bstpr > 120 and readfile("GUTC") == 0:
            countg3 += 1
            if countg3 == 4:
                bf3statusg = 1
                numg1 = 100
                numg2 = 100
                numg3 = 0
                countg3 = 0
        else:
            countg3 = 0

        if bstpr < bstprmin*p4*0.97 and bstprmin>0 and nstprmin>0 and bf1statusg ==1 and bstpr > 120 and readfile("GUTA") == 0:
            bf1statusg = 100
            tg_log_sos("GUT-A fired")
            writefile("GUTA","1")
#            fire("GUT","A","02")
#            fire("GUT","A","02")
#            fire("GUT","A","02")
        if bstpr < bstprmin*p5*0.97 and bstprmin>0 and nstprmin>0 and bf2statusg ==1 and bstpr > 120 and readfile("GUTB") == 0:
            bf2statusg = 100
            tg_log_sos("GUT-B fired")
            writefile("GUTB","1")
#            fire("GUT","B","02")
#            fire("GUT","B","02")
#            fire("GUT","B","02")
        if bstpr < bstprmin*p6*0.97 and bstprmin>0 and nstprmin>0 and bf3statusg ==1 and bstpr > 120 and readfile("GUTC") == 0:
            bf3statusg = 100 
            tg_log_sos("GUT-C fired")
            writefile("GUTC","1")
#            fire("GUT","C","02")
#            fire("GUT","C","02")
#            fire("GUT","C","02")

        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf1statusg ==100 and bstpr > 10 and readfile("GUTA") == 1:
            tg_log_sos("GUT-A exited")
            writefile("GUTA","100")
#            stop("GUT","A","02")
#            stop("GUT","A","02")
#            stop("GUT","A","02")
        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf2statusg ==100 and bstpr > 10 and readfile("GUTB") == 1:
            tg_log_sos("GUT-B exited")
            writefile("GUTB","100")
#            stop("GUT","B","02")
#            stop("GUT","B","02")
#            stop("GUT","B","02")
        if bstpr <= bstprmin and bstprmin>0 and nstprmin>0 and bf3statusg ==100 and bstpr > 10 and readfile("GUTC") == 1:
            tg_log_sos("GUT-C exited")
            writefile("GUTC","100")
#            stop("GUT","C","02")
#            stop("GUT","C","02")
#            stop("GUT","C","02")
        #_____________________GUT FINISHES__________________________
        
        if bstpr > bstprmin*p1 and bstprmin>0 and nstprmin>0 and bstpr > 120 and (num1 <= 5 or num2 <= 5 or num3 <= 5):
            num1 = num1 + 1
            num2 = num2 + 1
            num3 = num3 + 1
            if num1 <= 1 or num2 <= 1 or num3 <= 1:
                tg_alert("Index:            BankNifty\n\nStraddle premium is spiking, wait for the cooldown to capture spike.\n\nMinimum Prem: "+str(round(bstprmin,2))+"\nCurrent Prem: "+str(round(bstpr,2))+"\nSpike in absolute points: "+str(round(bstpr-bstprmin,2))+"\n\nTrading the spike would be notified separately.")
#            tg_st("Bank Nifty Straddle premium is spiking, wait for the cooldown to capture spike. \nMinimum Prem: "+str(round(bstprmin,2))+"\nCurrent Prem: "+str(round(bstpr,2)))



#____________NIFTY Straddle Calculation starts here_____________________
#Similarly in future, a different account and a different server can track the spike in stocks as well, 
#of liquid stock options, and sell them for quick profit or loss. make a definition and get the sell 


        for scrip in noc['values']:
            if int(float(scrip["strprc"])) == int(float(nfatmstrike)):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                nstpr1=float(scripdata['lp'])+nstpr1
            if int(float(scrip["strprc"])) == int(float(nfatmstrike)-50):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                nstpr2=float(scripdata['lp'])+nstpr2
            if int(float(scrip["strprc"])) == int(float(nfatmstrike)+50):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                nstpr3=float(scripdata['lp'])+nstpr3
            if int(float(scrip["strprc"])) == int(float(nfatmstrike)+100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                nstpr4=float(scripdata['lp'])+nstpr4
            if int(float(scrip["strprc"])) == int(float(nfatmstrike)-100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                nstpr5=float(scripdata['lp'])+nstpr5
        
        values = [nstpr1, nstpr2, nstpr3, nstpr4, nstpr5]
        values.sort()
        non_zero_values = [v for v in values if v != 0]
        nstpr = min(non_zero_values)
        
        if nstpr>0:
            nstprmin = min(nstpr,nstprmin)

        nfs.info(nstpr)

#____________________NIFTY_______________________

        if nstpr > nstprmin*p1 and bstprmin > 0 and nstprmin > 0 and nf1status == 0 and nstpr > 50 and readfile("NIFA") == 0:
            count4 += 1
            if count4 == 4:
                nf1status = 1
                count4 = 0
                num4 = 0
        else:
            count4 = 0

        if nstpr > nstprmin*p2 and bstprmin > 0 and nstprmin > 0 and nf2status == 0 and nstpr > 50 and readfile("NIFB") == 0:
            count5 += 1
            if count5 == 4:
                nf2status = 1
                num4 = 100
                num5 = 0
                count5 = 0
        else:
            count5 = 0

        if nstpr > nstprmin*p3 and bstprmin > 0 and nstprmin > 0 and nf3status == 0 and nstpr > 50 and readfile("NIFC") == 0:
            count6 += 1
            if count6 == 4:
                nf3status = 1
                num4 = 100
                num5 = 100
                num6 = 0
                count6 = 0
        else:
            count6 = 0


        if nstpr < nstprmin*p1*0.97 and bstprmin>0 and nstprmin>0 and nf1status ==1 and nstpr > 50 and readfile("NIFA") == 0:
            nf1status = 100
            trailslnf = 1
            tg_log_sos("Straddle for Nifty-A fired")
            tg_alert("Selling "+str(round((p1-1)*100,0))+"% Spike Nifty Straddle now to capture spike.")
            writefile("NIFA","1")
            fire("NIF","A",sln1)
            fire("NIF","A",sln1)
            fire("NIF","A",sln1)
        if nstpr < nstprmin*p2*0.97 and bstprmin>0 and nstprmin>0 and nf2status ==1 and nstpr > 50 and readfile("NIFB") == 0:
            nf2status = 100
            trailslnf = 1
            tg_log_sos("Straddle for Nifty-B fired")
            tg_alert("Selling "+str(round((p2-1)*100,0))+"% Spike Nifty Straddle now to capture spike.")
            writefile("NIFB","1")
            fire("NIF","B",sln2)
            fire("NIF","B",sln2)
            fire("NIF","B",sln2)
        if nstpr < nstprmin*p3*0.97 and bstprmin>0 and nstprmin>0 and nf3status ==1 and nstpr > 50 and readfile("NIFC") == 0:
            nf3status = 100
            trailslnf = 1
            tg_log_sos("Straddle for Nifty-C fired")
            tg_alert("Selling "+str(round((p3-1)*100,0))+"% Spike Nifty Straddle now to capture spike.")
            writefile("NIFC","1")
            fire("NIF","C",sln3)
            fire("NIF","C",sln3)
            fire("NIF","C",sln3)

        if nstpr <= nstprmin and bstprmin>0 and nstprmin>0 and nf1status ==100 and nstpr > 10 and readfile("NIFA") == 1:
            tg_log_sos("Straddle for Nifty-A exited with SL "+str(float(sl1)/10)+"%")
            writefile("NIFA","100")
#            stop("DEF","A",sl1)
        if nstpr <= nstprmin and bstprmin>0 and nstprmin>0 and nf2status ==100 and nstpr > 10 and readfile("NIFB") == 1:
            tg_log_sos("Straddle for Nifty-B exited with SL "+str(float(sl1)/10)+"%")
            writefile("NIFB","100")
#            stop("DEF","B",sl2)
        if nstpr <= nstprmin and bstprmin>0 and nstprmin>0 and nf3status ==100 and nstpr > 10 and readfile("NIFC") == 1:
            tg_log_sos("Straddle for Nifty-C exited with SL "+str(float(sl1)/10)+"%")
            writefile("NIFC","100")
#            stop("DEF","C",sl3)
        
        if nstpr > nstprmin*p1 and bstprmin>0 and nstprmin>0 and nstpr > 50 and (num4 <= 5 or num5 <= 5 or num6 <= 5):
            num4 = num4 + 1
            num5 = num5 + 1
            num6 = num6 + 1
            if num4 <= 1 or num5 <= 1 or num6 <= 1:
                tg_alert("Index:            Nifty\n\nStraddle premium is spiking, wait for the cooldown to capture spike.\n\nMinimum Prem: "+str(round(nstprmin,2))+"\nCurrent Prem: "+str(round(nstpr,2))+"\nSpike in absolute points: "+str(round(nstpr-nstprmin,2))+"\n\nTrading the spike would be notified separately.")
#            tg_st("Nifty Straddle premium is spiking, wait for the cooldown to capture spike. \nMinimum Prem: "+str(round(nstprmin,2))+"\nCurrent Prem: "+str(round(nstpr,2)))


#_______________________FIN_NIFTY calculation here____________________________

        for scrip in foc['values']:
            if int(float(scrip["strprc"])) == int(float(fnatmstrike)):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                fstpr1=float(scripdata['lp'])+fstpr1
            if int(float(scrip["strprc"])) == int(float(fnatmstrike)-50):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                fstpr2=float(scripdata['lp'])+fstpr2
            if int(float(scrip["strprc"])) == int(float(fnatmstrike)+50):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                fstpr3=float(scripdata['lp'])+fstpr3
            if int(float(scrip["strprc"])) == int(float(fnatmstrike)+100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                fstpr4=float(scripdata['lp'])+fstpr4
            if int(float(scrip["strprc"])) == int(float(fnatmstrike)-100):
                scripdata = user_obj.get_quotes(exchange=scrip['exch'], token=scrip['token'])
                fstpr5=float(scripdata['lp'])+fstpr5
        
        values = [fstpr1, fstpr2, fstpr3, fstpr4, fstpr5]
        values.sort()
        non_zero_values = [v for v in values if v != 0]
        fstpr = min(non_zero_values)

        if fstpr>0:
            fstprmin = min(fstpr,fstprmin)

        ffs.info(fstpr)
#____________________Fin-NIFTY_______________________

        if fstpr > fstprmin*pf1 and bstprmin > 0 and nstprmin > 0 and fstprmin > 0 and fn1status == 0 and fstpr > 50 and readfile("FINA") == 0:
            count7 += 1
            if count7 == 4:
                fn1status = 1
                count7 = 0
                num7 = 0
        else:
            count7 = 0

        if fstpr > fstprmin*pf2 and bstprmin > 0 and nstprmin > 0 and fstprmin > 0 and fn2status == 0 and fstpr > 50 and readfile("FINB") == 0:
            count8 += 1
            if count8 == 4:
                fn2status = 1
                num7 = 100
                num8 = 0
                count8 = 0
        else:
            count8 = 0

        if fstpr > fstprmin*pf3 and bstprmin > 0 and nstprmin > 0 and fstprmin > 0 and fn3status == 0 and fstpr > 50 and readfile("FINC") == 0:
            count9 += 1
            if count9 == 4:
                fn3status = 1
                num7 = 100
                num8 = 100
                num9 = 0
                count9 = 0
        else:
            count9 = 0


        if fstpr < fstprmin*pf1*0.97 and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn1status ==1 and fstpr > 50 and readfile("FINA") == 0:
            fn1status = 100
            trailslfn = 1
            writefile("FINA","1")
            tg_log_sos("Straddle FIN-A fired")
            tg_alert("Selling "+str(round((pf1-1)*100,0))+"% FinNifty Straddle now to capture spike.")
            fire("FIN","A",sl1)
            fire("FIN","A",sl1)
            fire("FIN","A",sl1)
        if fstpr < fstprmin*pf2*0.97 and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn2status ==1 and fstpr > 50 and readfile("FINB") == 0:
            fn2status = 100
            trailslfn = 1
            writefile("FINB","1")
            tg_log_sos("Straddle FIN-B fired")
            tg_alert("Selling "+str(round((pf2-1)*100,0))+"% FinNifty Straddle now to capture spike.")
            fire("FIN","B",sl2)
            fire("FIN","B",sl2)
            fire("FIN","B",sl2)
        if fstpr < fstprmin*pf3*0.97 and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn3status ==1 and fstpr > 50 and readfile("FINC") == 0:
            fn3status = 100
            trailslfn = 1
            writefile("FINC","1")
            tg_log_sos("Straddle FIN-C fired")
            tg_alert("Selling "+str(round((pf3-1)*100,0))+"% FinNifty Straddle now to capture spike.")
            fire("FIN","C",sl3)
            fire("FIN","C",sl3)
            fire("FIN","C",sl3)


        if fstpr <= fstprmin and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn1status ==100 and fstpr > 10 and readfile("FINA") == 1:
            tg_log_sos("Test FINA exited")
            writefile("FINA","100")
        if fstpr <= fstprmin and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn2status ==100 and fstpr > 10 and readfile("FINB") == 1:
            tg_log_sos("Test FINB exited")
            writefile("FINB","100")
        if fstpr <= fstprmin and bstprmin>0 and nstprmin>0 and fstprmin > 0 and fn3status ==100 and fstpr > 10 and readfile("FINC") == 1:
           tg_log_sos("Test FINC exited")
           writefile("FINC","100")
        
        if fstpr > fstprmin*pf1 and bstprmin>0 and nstprmin>0 and fstprmin > 0 and (num7 <= 5 or num8 <= 5 or num9 <= 5):
            num7 = num7 + 1
            num8 = num8 + 1
            num9 = num9 + 1
            if num7 <= 1 or num8 <= 1 or num9 <= 1:
                tg_alert("Index:            FinNifty\n\nStraddle premium is spiking, wait for the cooldown to capture spike.\n\nMinimum Prem: "+str(round(fstprmin,2))+"\nCurrent Prem: "+str(round(fstpr,2))+"\nSpike in absolute points: "+str(round(fstpr-fstprmin,2))+"\n\nTrading the spike would be notified separately.")
#            tg_st("FinNifty Straddle premium is spiking, wait for the cooldown to capture spike. \nMinimum Prem: "+str(round(fstprmin,2))+"\nCurrent Prem: "+str(round(fstpr,2)))
        
#Write and save min straddle premium in a safe place when code is running
        if dt.now().second % 50 < 10:
            with open('/home/ec2-user/newalgo/personal/minprembf.txt', 'w') as f:
                f.write(str(bstprmin))
            with open('/home/ec2-user/newalgo/personal/minpremnf.txt', 'w') as f:
                f.write(str(nstprmin))
            with open('/home/ec2-user/newalgo/personal/minpremfn.txt', 'w') as f:
                f.write(str(fstprmin))
        
        #send this to VIX analyser
        if dt.now().hour < 10 and dt.now().minute<=20:
            with open ('/home/ec2-user/newalgo/personal/vix/inputdata.txt', 'w') as f:
                vix = float(get_quote(user_obj, 'NSE', find_scrip_details("INDIAVIX", 'INDEX', 'token'), 'ltp'))
                f.write(str(vix)+"\n"+str(nfatmstrike)+"\n"+str(nstpr))

        current_time = dt.now().time()
        end_time = dt.strptime("09:19", "%H:%M").time()
        if current_time <= end_time:
            time.sleep(0.5)
        else:
            time.sleep(12)
opt()
