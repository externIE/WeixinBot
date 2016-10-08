#!/usr/bin/env python
# coding: utf-8
import os
import json
import threading

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
Status_White 		= 0
Status_QiangZhuang 	= 1
Status_XiaZhu 		= 2
Status_QiangBao 	= 3
Status_Wait         = 4
#游戏管理机器人,处理某个群的群消息
class EXBOT(object):
	

	def __init__(self, groupid, groupname, admin, adminname, weixin):
		self.groupid = groupid
		self.groupname = groupname
		self.admin = admin
		self.adminname = adminname
		self.weixin = weixin
		self.qiangzhuangtimelimit = 20
		self.xiazhutimelimit = 20
		self.qiangbaotimelimit = 20
		self.status = Status_White

		self.qzPlayerList = []
		self.xzPlayerList = []

		self.timeLine = None

		self.waitForRedBaoProfile = True
		self.qiangbaoCostTime = 0

		self.loadConfig()
		self.loadPlayerInfo()

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
		self.blList = config["倍率"]
		self.maxBL = self.blList["豹子"]

		self.tpOutZhuangTip = config["溢庄提醒"]
		self.tpOutScoreTip = config["溢分提醒"]

		self.tpNewboutTip = config["新局提示"]
		self.tpPlayersScoreList = config["玩家积分榜"]
		self.tpPlayerScore = config["玩家积分"]
		self.tpQZEnd = config["抢庄结束"]

		self.tpXZTip = config["下分提示"]
		self.tpXZList = config["下分列表"]
		self.tpXZRes = config["下分结果"]

		self.tpFBTip = config["发包提示"]
		self.tpEndFBTip = config["提醒发包人发布结果"]

		self.tpNPRez = config["抢包人"]
		self.tpFPRez = config["未抢包人"]
		self.tpRez = config["抢包结束"]

		self.strEndGame = config["结束游戏提示"]

	def loadPlayerInfo(self):
		filename = 'playerinfo.json'
		dirname = os.path.join(os.getcwd(), 'playerinfo')
		fn = os.path.join(dirname, filename)
		with open(fn, 'r') as file:
			self.jsonPlayersInfo = config = json.load(file, object_hook=_decode_dict)
		self.playersinfo = config['playersinfo']
		self.playersName = []
		for index, playerinfo in enumerate(self.playersinfo):
			self.playersName.append(playerinfo['name'])


	def setStatus(self, status):
		self.status = status

	def isStatus(self, status):
		return self.status == status

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

	def getPlayerScoreByName(self, name):
		for index, playerinfo in enumerate(self.playersinfo):
			if playerinfo["name"] == name:
				return playerinfo['score']
			else:
				return 0

	def setPlayerScoreByName(self, name, score):
		for index, playerinfo in enumerate(self.playersinfo):
			if playerinfo["name"] == name:
				self.playersinfo[index]["score"] = int(score)
				break

	def setPlayerDiffScoreByName(self, name, diffScore):
		for index, playerinfo in enumerate(self.playersinfo):
			if playerinfo["name"] == name:
				self.playersinfo[index]["score"] += int(diffScore)
				break

	def restorePlayersScore(self):
		filename = 'playerinfo.json'
		dirname = os.path.join(os.getcwd(), 'playerinfo')
		fn = os.path.join(dirname, filename)
		with open(fn, 'w') as file:
			file.write(json.dumps(self.jsonPlayersInfo, indent=4))

	def sendPlayersScore(self):
		template = self.tpPlayersScoreList
		content = ''
		for playerinfo in self.playersinfo:
			content += self.tpPlayerScore%(playerinfo['name'], playerinfo['score'])
		txt = template%(content,)
		if self.sendMsgToMyGroup(text):
			print '玩家积分发送成功'
		else:
			print '[error!] 玩家积分发送失败，正在重新发送...'
			self.sendPlayersScore()

	def startQZ(self):
		#发送新局消息
		template = self.tpNewboutTip
		text = template%(self.adminname, self.qiangzhuangtimelimit)
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_QiangZhuang)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.startQZ()

	def endQZ(self):
		#抢庄结束
		if len(self.qzPlayerList) == 0:
			#没有人抢庄，游戏提前结束
			self.sendMsgToMyGroup('[*]没人抢庄，游戏提前结束')
			self.initData()
			return False
		template = self.tpQZEnd
		zPlayerName = None
		zZhu = -1000
		for name, zhu in enumerate(self.qzPlayerList):
			if zhu > zZhu:
				zPlayerName = name
				zZhu = zhu

		self.zPlayerName = zPlayerName
		self.zZhu = zZhu

		text = template%(zPlayerName)
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_Wait)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.endQZ()


	def startXZ(self):
		#开始下注
		template = self.tpXZTip
		text = template%(self.adminname, self.xiazhutimelimit, self.maxBL)
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_XiaZhu)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.startXZ()

	def endXZ(self):
		#下注结束
		if len(self.xzPlayerList) == 0:
			#没人下分，游戏提前结束
			self.sendMsgToMyGroup["[*]没人下分，游戏提前结束"]
			self.initData()
			return False
		template = self.tpXZList
		content = ''
		for name, zhu in enumerate(self.xzPlayerList):
			content += self.tpXZRes%(name, zhu)
		text = template%(content,)
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_Wait)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.endXZ()

	def startFB(self):
		#开始发包
		template = self.tpFBTip
		text = template%(self.adminname, )
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_QiangBao)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.startFB()

	def endFB(self):
		#提醒发包人应该结束抢包了
		template = self.tpEndFBTip
		text = template%(self.adminname, )
		if self.sendMsgToMyGroup(text):
			pass
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.endFB()

	def showResult(self):
		#发送结果
		self.calcType()
		self.buildResult()
		self.restorePlayersScore()
		normalResults = ""
		for name, bl in enumerate(self.blPlayerList):
			strName = name
			strZX = "庄" if name == self.zPlayerName else "闲"
			strDS = str(self.dsPlayerList[name])
			strType = self.typePlayerList[name]
			strBL = str(self.blPlayerList[name])
			strDiff = str(self.diffPlayerList[name])
			strScore = self.getPlayerScoreByName(name)
			normalResults += self.tpNPRez%(strName,strZX,strDS,strType,strBL,strDiff,strScore)

		abortResults = ""
		for name, xzScore in enumerate(self.xzPlayerList):
			#看看谁下注但没有抢包
			if name not in self.blPlayerList.keys():
				strName = name
				strZX = "庄" if name == self.zPlayerName else "闲"
				strDS = "*"
				strType = "*"
				strBL = "*"
				strDiff = str(self.diffPlayerList[name])
				strScore = self.getPlayerScoreByName(name)
				abortResults += self.tpFPRez%(strName,strZX,strDS,strType,strBL,strDiff,strScore)

		template = self.tpRez
		text = template%(self.normalResults, self.abortResults)
		if self.sendMsgToMyGroup(text):
			pass
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.showResult()

	def initData(self):
		pass


	def handleQiangZhuang(self, memberID, memberName, memberSay):
		if memberSay.isdigit():
			if int(memberSay) <= self.getPlayerScoreByName(memberName):
				if memberName not in self.qzPlayerList.keys():
					self.qzPlayerList[memberName] = int(memberSay)
				else:
					self.qzPlayerList[memberName] = self.qzPlayerList[memberName] if self.qzPlayerList[memberName] > int(memberSay) else int(memberSay)
			else:
				template = self.tpOutZhuangTip
				text = template%(memberName, self.getPlayerScoreByName(memberName))
				self.sendMsgToMyGroup(text)
		if memberSay == '取消':
			if memberName in self.qzPlayerList.keys():
				self.qzPlayerList.pop(memberName)

	def handleXiaZhu(self, memberID, memberName, memberSay):
		if memberSay.isdigit():
			if memberName == self.zPlayerName:
				self.sendMsgToMyGroup('[@%s ]庄不参与下注'%(memberName,))
				return
			if int(memberSay)*self.maxBL <= self.getPlayerScoreByName(memberName):
				if memberName not in self.qzPlayerList.keys():
					self.xzPlayerList[memberName] = int(memberSay)
				else:
					self.xzPlayerList[memberName] = self.qzPlayerList[memberName] if self.xzPlayerList[memberName] > int(memberSay) else int(memberSay)
			else:
				template = self.tpOutScoreTip
				text = template%(memberName, self.getPlayerScoreByName(memberName)/self.maxBL)
				self.sendMsgToMyGroup(text)
		if memberSay == '取消':
			if memberName in self.xzPlayerList.keys():
				self.xzPlayerList.pop(memberName)

	def handleRedBaoProfile(self, memberID, memberName, memberSay):
		if memberID == self.admin and memberName == self.adminname:
			if memberSay[:4] == '抢包情况' :
				ret = self.parseRedBaoProfile(memberSay)
				if ret :
					self.waitForRedBaoProfile = False
					self.setStatus(Status_White)
				else :
					return
		else:
			return

	def parseRedBaoProfile(self, memberSay):
		pattern = r'名字：\*(\S+)\* -- 点数：\*(\S+)\*'
		pm = re.findall(pattern, memberSay)
		self.dsPlayerList = {}
		for group in pm:
			self.dsPlayerList[group[0]] = group[1]
		if len(self.dsPlayerList) != 0 :
			return True
		else :
			return False

	def calcType(self):
		dsPlayerList = self.dsPlayerList
		self.typePlayerList = {}
		self.blPlayerList = {}
		for name, score in enumerate(dsPlayerList):
			num1, num2 = self.splitScore(score)
			if (num1 == 0 and num2 == 0) or (num1 == 1 and num2 == 0):
				#牛牛
				self.typePlayerList[name] = "牛牛"
				self.blPlayerList[name] = self.blList["牛牛"]
				continue
			if (num1 == 1 and num2 == 1) or (num1 == 2 and num2 == 2) or (num1 == 3 and num2 == 3):
				#豹子
				self.typePlayerList[name] = "豹子"
				self.blPlayerList[name] = self.blList["豹子"]
				continue
			self.typePlayerList[name] = "牛%d"%((num1+num2)%10,)
			self.blPlayerList[name] = self.blList["牛%d"%((num1+num2)%10,)]

	def buildResult(self):
		zBL = self.blPlayerList[self.zPlayerName]
		zPlayerName = self.zPlayerName
		self.diffPlayerList = {}
		self.diffPlayerList[zPlayerName] = 0
		for name, bl in enumerate(self.blPlayerList):
			#这一次循环先把所有输的闲家的钱收过来
			if zPlayerName == name :
				continue
			if bl <= zBL :
				#庄家赢
				xzScore = self.xzPlayerList[name]
				self.setPlayerDiffScoreByName(zPlayerName, xzScore*zBL)
				self.setPlayerDiffScoreByName(name, -xzScore*zBL)
				self.diffPlayerList[name] = -xzScore*zBL
				self.diffPlayerList[zPlayerName] += xzScore*zBL


		for name, xzScore in enumerate(self.xzPlayerList):
			#看看谁下注但没有抢包
			if name not in self.blPlayerList.keys():
				#按庄家的倍率赔
				self.setPlayerDiffScoreByName(zPlayerName, xzScore*zBL)
				self.setPlayerDiffScoreByName(name, -xzScore*zBL)
				self.diffPlayerList[name] = -xzScore*zBL
				self.diffPlayerList[zPlayerName] += xzScore*zBL

		xjWinTotal = 0
		xjWin = {}
		for name, bl in enumerate(self.blPlayerList):
			#这一次循环庄家赔钱
			if zPlayerName == name :
				continue
			if bl > zBL :
				#庄家赔
				xzScore = self.xzPlayerList[name]
				self.setPlayerDiffScoreByName(zPlayerName, -xzScore*bl)
				self.setPlayerDiffScoreByName(name, xzScore*bl)

				self.diffPlayerList[name] = xzScore*zBL
				self.diffPlayerList[zPlayerName] += -xzScore*zBL

				xjWin[name] = xzScore*bl
				xjWinTotal += xzScore*bl

		if self.getPlayerScoreByName(zPlayerName) < 0 :
			#如果发现庄家的钱小于零，说明不够赔，那么闲家应该吃水
			diffScore = self.getPlayerScoreByName(zPlayerName)
			self.setPlayerDiffScoreByName(zPlayerName, -diffScore)
			self.diffPlayerList[zPlayerName] += -diffScore
			for name, bl in enumerate(self.blPlayerList):
				#这一次循环庄家赔钱
				if zPlayerName == name :
					continue
				if bl > zBL :
					#多余的钱应该补回给闲家
					xzScore = self.xzPlayerList[name]
					self.setPlayerDiffScoreByName(name, diffScore*xjWin[name]*xjWinTotal)
					self.diffPlayerList[name] += diffScore*xjWin[name]*xjWinTotal



	def splitScore(self, score):
		pm = re.search(r'.(\d)(\d)', score)
		return int(pm.group(1)), int(pm.group(2))

	def startTimeLine(self):
		self.startLine = True
		self.timeLine = threading.Thread(target=self.commander)
		self.timeLine.setDaemon(True)
		self.timeLine.start()

	def stopTimeLine(self):
		self.startLine = False
		self.timeLine = None
		text = self.strEndGame
		if self.sendMsgToMyGroup(text):
			self.setStatus(Status_White)
		else:
			print '[error!] 发送开始消息失败,正在重新发送...'
			self.stopTimeLine()

	def commander(self):
		while self.startLine:
			self.sendPlayersScore()
			time.sleep(2)

			self.startQZ()
			time.sleep(self.qiangzhuangtimelimit)
			ret = self.endQZ()
			if not ret:
				break

			time.sleep(2)

			self.startXZ()
			time.sleep(self.xiazhutimelimit)
			ret = self.endXZ()
			if not ret:
				break

			time.sleep(2)

			self.startFB()
			while self.waitForRedBaoProfile:
				self.qiangbaoCostTime += 0.1
				if self.qiangbaoCostTime % self.qiangbaotimelimit == 0 :
					self.endFB()
				#每0.01秒检查一次
				time.sleep(0.1)

			time.sleep(2)

			self.showResult()
			time.sleep(5)



    #处理消息
	def handleMsg(self, msg):
		if msg['FromUserName'] != self.groupid:
			#丢弃不是自己管理的消息
			return False
		print 'Robot Catch Msg'
		weixin = self.weixin
		memberID, memberName, memberSay = self.parseMsg(msg)
		memberSay = memberSay.strip()
		if memberName in self.playersName:
			#丢弃不在玩家列表中的人的消息
			print memberName, "不在游戏中..."
			print '全部成员', self.playersName
			return True
		if memberID == self.admin and memberSay == '结束游戏' :
			self.stopTimeLine()

		if self.isStatus(Status_White):
			if memberID == self.admin and memberSay == '开始游戏' :
				self.startTimeLine()
		elif self.isStatus(Status_QiangZhuang):
			self.handleQiangZhuang(memberID, memberName, memberSay)
		elif self.isStatus(Status_XiaZhu):
			self.handleXiaZhu(memberID, memberName, memberSay)
		elif self.isStatus(Status_QiangBao):
			self.handleRedBaoProfile(memberID, memberName, memberSay)
		return True
