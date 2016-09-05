#!/usr/bin/env python
# -*- coding: utf-8 -*-
import persistent
import json

from uuid import uuid4
from telegram import InlineQueryResultCachedVoice

# Voice Class
class VoiceFile(persistent.Persistent):
	"""This object represents a Voice Sound.

	Attributes:
		id (str): uuid4 string
		type (str): 'voice'
		title (str): Title for the voice sound file
		description (str): Description for the voice sound file
		tags (str): Tags separated by comma, for improved search results
		username (str): User who uploaded the voice sound file
		file_id (str): Id for the voice sound file stored in telegram

	Args:
		title (str):
		description (str):
		tags (str):
		username (str):
		file_id (str):
	"""

	def __init__(self, title = "", file_id = "", 
				description = None, 
				tags = "", 
				username = None
				):

		self.id = "%s" % uuid4()
		self.type = "voice"

		self.title = title
		self.file_id = file_id

		self.description = description
		self.tags = tags
		self.username = username

	def voice(self):
		return InlineQueryResultCachedVoice(id = self.id,
											title = self.title,
											voice_file_id = self.file_id,
											type = self.type,
											input_message_content = self.description
											)
	def vars(self):
		# Could use vars(self) too
		# but __dict__ its more readable
		# because we return a dict()
		return self.__dict__

	def json(self):
		return json.dumps(self.vars())

	def __str__(self):
		return self.json()