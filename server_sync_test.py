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
from models.server import Server, ServerDetail, AssetConfigs, model_to_dict, ServerTag, Tag

import time, datetime, requests

#aliyun_ecs_update()
#time.sleep(2)
#aws_ec2_update()
#time.sleep(2)
#qcloud_cvm_update()
#time.sleep(2)
#huawei_ecs_update()
#time.sleep(2)
#ucloud_uhost_update()

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

def GetServerDetail():
    serverdetaillist = []
    with DBContext('r') as session:
        sdlist = session.query(ServerDetail).all()
        for sd in sdlist:
            datadict = model_to_dict(sd)
            serverdetaillist.append(datadict)
    return serverdetaillist

def GetServerState(server_list, server_ip):
    for server in server_list:
        if server_ip == server["ip"]:
            return server["instance_state"]
    return None

def CheckServer():
    expired_server = {}
    normal_server = {}
    provider_list = GetProviderList()
    server_detail_list = GetServerDetail()
    with DBContext('r') as session:
        serverlist = session.query(Server).filter(Server.region != "")
        for server in serverlist:
            data_dict = model_to_dict(server)
            server_state = GetServerState(server_detail_list, data_dict["ip"])
            if server_state == "Stopped":
                continue
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
        print(expired_server)
        print(normal_server)

if __name__ == "__main__":
    #TgSendMsg("封锁又延期了\n你还好吗？")
    #CheckServer()
    #print("Begin".ljust(50, '.'))
    #aliyun_ecs_update()
    with DBContext('r') as session:
        #sl = session.query(Server, ServerDetail).filter(Server.public_ip == ServerDetail.ip).all()
        #for s,sd in sl:
        #    print(s.hostname, s.idc, s.state, sd.instance_state, sd.ip, s.ip)
        count = session.query(Server).filter(Server.state != "Stopped").outerjoin(ServerTag, Server.id == ServerTag.server_id
                                                        ).outerjoin(Tag, Tag.id == ServerTag.tag_id).count()
        print(count)
    #print("End".ljust(50, '.'))