#!/usr/bin/env python
# coding: utf-8
def calcAnswer(content):
	answer = None
	if content.find('凌志') != -1:
		answer = '星翔是傻钟最爱的人'
	if content.find('丁星') != -1 or content.find('星翔') != -1:
		answer = '沙中是星翔最爱的人儿'
	return answer
