#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact : northdipperbig@gmail.com
Author  : North Star
Date    : 2020/05/12
Desc    : 
    Update server from Cloud platform
    Check server expired time
    Send telegram message to group
"""

from libs.aliyun.ecs import main as aliyun_ecs_update
from libs.aliyun.boss import main as aliyun_boss
from libs.huaweiyun.huawei_ecs import main as huawei_ecs_update
from libs.aws.ec2 import main as aws_ec2_update
from libs.qcloud.cvm import main as qcloud_cvm_update
from libs.ucloud.uhost import main as ucloud_uhost_update
from libs.db_context import DBContext
from models.server import Server, ServerDetail, AssetConfigs, model_to_dict

import time, datetime, requests

aliyun_ecs_update()
time.sleep(2)
aws_ec2_update()
time.sleep(2)
qcloud_cvm_update()
time.sleep(2)
huawei_ecs_update()
time.sleep(2)
ucloud_uhost_update()

CurrentDateTime = datetime.datetime.now()

TgApiToken = "1063249430:AAFjdQYajKzIX70RgYZnMv8Y0zIVtpqZ-ps"
TgChatId = "-320846845"
#TgChatId = "-403702424"

def TgSendMsg(msg):
    url = "https://api.telegram.org/bot"+TgApiToken+"/sendMessage"
    Pdata = {"chat_id": TgChatId, "text": msg}
    if msg != "":
        r = requests.post(url, data=Pdata)
        return r.json()

def GetProviderList():
    ret = []
    with DBContext('r') as session:
        providerlist = session.query(AssetConfigs)
        for provider in providerlist:
            data_dict = model_to_dict(provider)
            subaccount = data_dict["remarks"].split(";")[0]
            s = {}
            s["id"] = data_dict["id"]
            s["sub_account"] = subaccount
            ret.append(s)
    return ret

def GetProviderAccount(provider_list, provider_id):
    for p in provider_list:
        if provider_id == p["id"]:
            return p["sub_account"]
    return None

def CheckServer():
    expired_server = {}
    normal_server = {}
    provider_list = GetProviderList()
    with DBContext('w') as session:
        serverlist = session.query(Server).filter(Server.region != "")
        for server in serverlist:
            data_dict = model_to_dict(server)
            expireddays = abs((CurrentDateTime - data_dict["expired_time"]).days) - 1
            AliyunSubAccount = GetProviderAccount(provider_list, data_dict["provider_id"])
            if expireddays < 7:
                if not expired_server.get(AliyunSubAccount):
                    expired_server[AliyunSubAccount] = []
                s = {}
                s["hostname"] = data_dict["hostname"]
                s["ip"] = data_dict["ip"]
                s["expired_time"] = data_dict["expired_time"]
                s["expired_days"] = expireddays
                expired_server[AliyunSubAccount].append(s)
                
                #print(data_dict["hostname"], data_dict["ip"], data_dict["expired_time"], "........")
                #print(msg)
                #TgSendMsg(msg)
                #expired_server.append(msg)
            else:
                if not normal_server.get(AliyunSubAccount):
                    normal_server[AliyunSubAccount] = []
                s = {}
                s["hostname"] = data_dict["hostname"]
                s["ip"] = data_dict["ip"]
                s["expired_time"] = data_dict["expired_time"]
                s["expired_days"] = expireddays
                normal_server[AliyunSubAccount].append(s)
                #print(data_dict["hostname"], data_dict["ip"], data_dict["expired_time"], "_______")
                #normal_server.append(msg)
        #过期服务器发送
        for i in expired_server.keys():
            msg = ""
            for j in expired_server[i]:
                msg = """=============================
服务器名称： {}
服务器地址： {}
到期时间  ： {}
剩余时间  ： {}天
""".format(j["hostname"], j["ip"], j["expired_time"], j["expired_days"]) + msg
            TgSendMsg("阿里云账号 {} 即将到期服务器：\n".format(i) + msg)
        
        for i in normal_server.keys():
            msg = ""
            for j in normal_server[i]:
                msg = "服务器【{}】剩余 {} 天\n".format(j["hostname"],j["expired_days"]) + msg
            TgSendMsg("阿里云账号 {} 正常服务器：\n".format(i) + msg)
    aliyun_balance = aliyun_boss()
    msg = ""
    for v in aliyun_balance:
        account_name = GetProviderAccount(provider_list, v['provider_id'])    
        msg = "阿里云账户{}余额为{}：{}元\n".format(account_name, v['Currency'], v['AvailableCashAmount']) + msg
    TgSendMsg("阿里云账户余额情况：\n"+msg)

if __name__ == "__main__":
    #TgSendMsg("封锁又延期了\n你还好吗？")
    CheckServer()