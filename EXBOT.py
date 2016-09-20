#!/usr/bin/env python
# coding: utf-8
import os
import json

def calcAnswer(content):
	answer = None
	if content.find('凌志') != -1:
		answer = '星翔是傻钟最爱的人'
	if content.find('丁星') != -1 or content.find('星翔') != -1:
		answer = '沙中是星翔最爱的人儿'

	return answer


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

#游戏管理机器人,处理某个群的群消息
class EXBOT(object):
	Status_White 		= 0
	Status_QiangZhuang 	= 1
	Status_XiaZhu 		= 2
	Status_QiangBao 	= 3

	def __init__(self, groupid, groupname, admin, adminname, weixin):
		self.groupid = groupid
		self.groupname = groupname
		self.admin = admin
		self.adminname = adminname
		self.weixin = weixin
		self.qiangzhuangtimelimit = 20
		self.xiazhutimelimit = 20
		self.qiangbaotimelimit = 20
		self.status = EXBOT.Status_White
		self.loadConfig()

	def __str__(self):
		description = \
		"=========================\n"\
		"[#] 我是［" + str(self.groupname) + "］群的机器人\n"\
		"[#] 该群的管理员是［" + str(self.adminname) + "］\n"\
		"========================="
		return description

	def loadConfig(self):
		filename = 'config.json'
		dirname = os.path.join(os.getcwd(), 'config')
		fn = os.path.join(dirname, filename)
		with open(fn, 'r') as file:
			config = json.load(file, object_hook=_decode_dict)
		self.qiangzhuangtimelimit = config["QiangZhuangTimeLimit"]
		self.xiazhutimelimit = config["XiaZhuTimeLimit"]
		self.qiangbaotimelimit = config["QiangBaoTimeLimit"]
		self.newbouttip = config["NewBoutTip"]

	def setStatus(self, status):
		self.status = status

    #向自己管理的组里面发送消息
	def sendMsgToMyGroup(self, text):
		weixin = self.weixin
		if not weixin :
			print '[error!] connector is none'
			return
		return weixin.webwxsendmsg(text, self.groupid)

	def parseMsgContent(self, content):
		li = content.split(':<br/>')
		fromUserName = li[0]
		msgContent = li[1]
		return fromUserName, msgContent

	def parseMsg(self, msg):
		content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')
		memberID, memberSay = self.parseMsgContent(content)
		memberName = self.weixin.getUserRemarkName(memberID)
		return memberID, memberName, memberSay

	def startGame(self):
		#发送新局消息
		template = self.newbouttip
		text = template%(self.adminname, self.qiangzhuangtimelimit)
		self.sendMsgToMyGroup(text)

    #处理消息
	def handleMsg(self, msg):
		if msg['FromUserName'] != self.groupid:
			#丢弃不是自己管理的消息
			return False
		weixin = self.weixin
		memberID, memberName, memberSay = self.parseMsg(msg)
		if memberID == self.admin and memberSay == '开始游戏' :
			self.startGame()
		return True
