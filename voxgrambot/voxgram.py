#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to post voice message to Telegram
# Made by Camilo Castro <camilo@ninjas.cl>

"""
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import ZODB, ZODB.FileStorage
import persistent
import transaction

import emoji
import ascii_data

import logging

import requests

import config

from voicefile import VoiceFile

from telegram import ParseMode, InlineQueryResultCachedVoice, InputTextMessageContent

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, ConversationHandler, \
							MessageHandler, Filters, RegexHandler

from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler

# Emojis
esmile = u'\U0001F60A'
ewink = u'\U0001F609'
eastonished = u'\U0001F632'
erobot = u'\U0001F916'
eok = u'\U0001F44C'
ethumbs = u'\U0001F44D'
emic = u'\U0001F3A4'
emoai = u'\U0001F5FF'
ewarning = u'\U000026A0'
echile =  u'\U0001F1E8\U0001F1F1'
eskull = u'\U0001F480'
erocket = u'\U0001F680'
estar = u'\U0001F31F'
esparkles = u'\U00002728'
eparty = u'\U0001F389'
econfetti = u'\U0001F38A'
eheart = u'❤️'

# Enable logging
debug = True

supported_keys = [
        'asctime',
        'created',
        'filename',
        'funcName',
        'levelname',
        'levelno',
        'lineno',
        'module',
        'msecs',
        'message',
        'name',
        'pathname',
        'process',
        'processName',
        'relativeCreated',
        'thread',
        'threadName'
      ]

log_format = lambda x: ['%({0:s})'.format(i) for i in x]

custom_format = ' '.join(log_format(supported_keys))

formatter = jsonlogger.JsonFormatter(custom_format)

handler = RotatingFileHandler('logs/voxgram.log', maxBytes=10000000, backupCount=1)

handler.setFormatter(formatter)

level = logging.INFO

if debug:
    level = logging.DEBUG

handler.setLevel(level)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=level)

logger = logging.getLogger(__name__)

logger.addHandler(handler)


# Data Base Config
storage = ZODB.FileStorage.FileStorage('voxgram.db')
db = ZODB.DB(storage)
connection = db.open()
root = connection.root()

# The Process for Creating a New Sound
TITLE_STATE, DESCRIPTION_STATE, DESCRIPTION_AGAIN_STATE, \
TAGS_STATE, UPLOAD_STATE, TITLE_AGAIN_STATE, PRIVACY_SELECTION_STATE, \
RETRY_UPLOAD_STATE = range(8)

# The Process for Deleting a Sound
INPUT_EMOJI = range(1)

# create a map if needed
if not "voices" in root:
	root["voices"] = {}

# upload retry counter
max_retries = 10

if not "retries" in root:
	root["retries"] = {}

voices = root["voices"]

retries = root["retries"]

transaction.commit()

logger.info("DataBase Initialized")

# Data Base Functions
def resetRetriesForUser(username):
	
	retries[username] = 1

	root["retries"] = retries

	transaction.commit()

	logger.info("Retries reset for user %s" % username)

def getRetriesForUser(username):

	if not username in retries:
		resetRetriesForUser(username)
	
	logger.info("Retries for user %s" % str(retries[username]))
	
	return retries[username]

def setRetriesForUser(username, availableRetries):
	retries[username] = availableRetries
	transaction.commit()


def addVoice(username, voice):
	voices[username] = voice
	
	root["voices"] = voices
	
	transaction.commit()

	logger.info("Added voice for user %s" % username)

def deleteVoiceForUser(username):

	try:
		voice = voices[username]
		
		if voice != None:
			del voices[username]
			
			root["voices"] = voices

			transaction.commit()

			logger.info("Deleted voice for user %s" % username)

	except KeyError:
		logger.warn("Tried to delete voice for user %s but it wasn't found" % username)

def voiceForUser(username):
	voice = None

	try:
		voice = voices[username]
		logger.info("Fetched Voice %s" % voice)

	except KeyError:
		logger.warn("Could not retrieve voice for username %s" % username)

	if voice == None:
		voice = VoiceFile(title = "", file_id = "", username=username)
		addVoice(username, voice)

	return voice


# General Functions

def is_private_chat(bot, update):

	if update.message.chat.type == 'private':
		return True
	else:
		logger.info("Chat is not private")
	
		bot.send_message(update.message.chat_id,
						text = "\n" + eskull + \
						"Sorry, but for using this command you need to send me a private message. " \
						+ eskull + "\n"
						)
	
		return False

def escape_markdown(text):
    """Helper function to escape telegram markup symbols"""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def help(bot, update):
	logger.info("Sending the Start Message")
	bot.send_message(update.message.chat_id, 
					text=
					emoai + " V O X G R A M  B O T " + emoai + "\n\n"
					"Howdy!, I'm VoxGram Bot. " + ewink +
					"\nI store voice messages so you can send them " +
					"to your friends!.\n"  +
					"\nIf you want to search a voice message, " +
					"just type \n\n@voxgrambot <query>\n\n in a group chat.\n\n" +
					"\nIf you want to add a new sound start a private\n" +
					"conversation with me and type\n\n/new.\n\n" +
					"Other commands are \n\n/hear <emoji> \n\nand\n\n/delete <emoji>\n\n" +
					"When you want to hear and delete your sounds.\n\n" +
					"If you want your stats, just type\n/stats\n" +
					"\nWant to know /about my creator?\n"
					)

def inlinequery(bot, update):
	
	query = update.inline_query.query

	logger.info("Inline Query Received %s" % query)

	results = list()

	# Example Response
	#no_homo = VoiceFile(title = "No Homo", file_id = "AwADAQADEgAD2qz9Db1R-agaK9zjAg")
	#logger.debug(no_homo)
	#results.append(no_homo.voice())

	endpoint = config.voices + "?query=%s" % query

	params = {}
	
	#params = {"query" : query}

	try:
		response = requests.get(endpoint, data=params, auth=config.auth)
		
		logger.info("Got Response")

		logger.debug(response.text)

		if response.ok and response.status_code == 200:

			logger.debug("OK Response")
			
			data = response.json()
			data = data["data"]

			for voice_data in data:
				
				caption = "%s - %s" % (voice_data["emoji"], voice_data["tags"])

				voice = VoiceFile(title = voice_data["title"], tags=voice_data["tags"], file_id = voice_data["file_id"], caption=caption, emoji=voice_data["emoji"])

				logger.debug("Voice Result %s" % str(voice))

				results.append(voice.voice())

			logger.debug("Results %s" % results)

			bot.answerInlineQuery(update.inline_query.id, results=results)
		
		else:
			raise Exception("No Results Found")

	except Exception as e:
		logger.warn(e)
		bot.answerInlineQuery(update.inline_query.id, results=list())

def new_sound(bot, update):

	if not is_private_chat(bot, update):
		return ConversationHandler.END

	user = update.message.from_user
	
	logger.info("User %s started new sound conversation." % user.username)

	bot.send_message(update.message.chat_id,
					
					text = "Ok, before adding a new voice message\n" +
					"I need some basic info.\n\n" +
					"If you want to stop creating a new sound\n" +
					"just type /cancel \n\n" +
					
					emic + " We will begin creating a new sound.\n\n" +
					"Do you want to be private or be available to the world?\n\n" +
					"/private " + emoai + "\n"
					"/public " + estar + "\n"
					)

	deleteVoiceForUser(user.username)

	return PRIVACY_SELECTION_STATE
		


def private_chosen_step(bot, update):

	user = update.message.from_user

	logger.info("User %s sat the sound as private" % user.username)

	voice = voiceForUser(user.username)
	voice.public = False

	bot.send_message(update.message.chat_id, 
		text = "The sound will be private.\n" +
			"Now I need the title for the sound\n" + ewink +
			"\nPlease write a title with 50 characters or less.\n")

	return TITLE_STATE

def public_chosen_step(bot, update):

	user = update.message.from_user

	logger.info("User %s sat the sound as public" % user.username)

	bot.send_message(update.message.chat_id, 
		text = "The sound will be public.\n" +
			"Now I need the title for the sound\n" + ewink +
			"\nPlease write a title with 50 characters or less.\n")

	return TITLE_STATE


def title_step(bot, update):

	user = update.message.from_user
	
	logger.info("User %s will set the title for the new sound." % user.username)

	voice = voiceForUser(user.username)

	title = update.message.text

	if title == None:
		title = ""

	logger.debug("Title Given %s" % title)
	
	title = title.strip()

	if len(title) < 1:
		logger.info("User typed a too short title")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The title is too short.\n" +
			"Please write a title with at least 1 non whitespace character.\n"
			)

		return TITLE_STATE

	if len(title) > 50:
		logger.info("User typed a long title")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The title is too long.\n" +
			"Please write a title that contains 50 characters or less.\n"
			)

		return TITLE_STATE


	voice.title = title 
	logger.info("Voice object changed title %s" % voice)

	logger.info("All validations were ok.")
	bot.send_message(update.message.chat_id,
					text = ethumbs + " All right, '%s' seems like an awesome title. \n" % title +
					"\nNow we need an emoji for sending the sound quickly!.\n\n"
					)

	return DESCRIPTION_STATE

def title_again_step(bot, update):
	user = update.message.from_user
	
	logger.info("User %s will set the title for the new sound." % user.username)

	voice = voiceForUser(user.username)

	title = update.message.text

	if title == None:
		title = ""

	logger.debug("Title Given %s" % title)
	
	title = title.strip()

	if len(title) < 1:
		logger.info("User typed a too short title")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The title is too short.\n" +
			"Please write a title with at least 1 non whitespace character.\n"
			)

		return TITLE_AGAIN_STATE

	if len(title) > 50:
		logger.info("User typed a long title")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The title is too long.\n" +
			"Please write a title that contains 50 characters or less.\n"
			)

		return TITLE_AGAIN_STATE


	voice.title = title 
	logger.info("Voice object changed title %s" % voice)

	logger.info("All validations were ok.")

	bot.send_message(update.message.chat_id,
					text = ethumbs + " All right, '%s' seems like an awesome title. \n" % title +
					"\nNow please upload or foward me a voice message"
					)

	return uploadVoiceFile(bot, update)


def description_step(bot, update):
	user = update.message.from_user
	
	logger.info("User %s will set the description for the new sound." % user.username)

	voice = voiceForUser(user.username)

	description = update.message.text

	if description == None:
		description = ""

	logger.debug("Description Given %s" % description)
	
	description = list(description.strip())

	if len(description) < 1:
		logger.info("User typed a too short description")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The emoji is too short.\n" +
			"Please write a single emoji.\n"
			)

		return DESCRIPTION_STATE

	description = description[0]

	if description not in emoji.UNICODE_EMOJI:
			if description not in ascii_data.symbol_list:

				logger.info("User typed not an emoji")

				bot.send_message(update.message.chat_id,
					text = ewarning + "No emoji found.\n" +
					"Please write a single emoji.\n"
					)

				return DESCRIPTION_STATE

	voice.description = description
	logger.info("Voice object changed description %s" % voice)

	logger.info("All validations were ok.")
	bot.send_message(update.message.chat_id,
					text = ethumbs + " Superb!, '%s' looks like a really cool sound. \n" % description +
					"\nThe next step is assign some tags so people could search the sound more easily.\n\n" +
					"Please write 1 to 5 tags separated by comma.\n\n"
					"Example: dog, barking, animals, cute"
					"\n\nIf you want to skip this step write\n/skip\n"
					)

	return TAGS_STATE

def description_again_step(bot, update):

	user = update.message.from_user
	
	logger.info("User %s will set the description again for the new sound." % user.username)

	voice = voiceForUser(user.username)

	description = update.message.text

	if description == None:
		description = ""

	logger.debug("Description Given %s" % description)
	
	description = list(description.strip())

	if len(description) < 1:
		logger.info("User typed a too short description")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The emoji is too short.\n" +
			"Please write a single emoji.\n"
			)

		return DESCRIPTION_AGAIN_STATE
		
	description = description[0]

	if description not in emoji.UNICODE_EMOJI:
		if description not in ascii_data.symbol_list:
			logger.info("User typed not an emoji")

			bot.send_message(update.message.chat_id,
				text = ewarning + "No emoji found.\n" +
				"Please write a single emoji.\n"
				)

			return DESCRIPTION_AGAIN_STATE


	voice.description = description
	logger.info("Voice object changed description %s" % voice)

	logger.info("All validations were ok.")
	bot.send_message(update.message.chat_id,
					text = ethumbs + " Superb!, '%s' looks like a really cool sound. \n" % description +
					"\nPlease record a sound with your mic or foward me a voice message\n" +
					emic
					)

	return uploadVoiceFile(bot, update)

def skip_description_step(bot, update):
	
	logger.info("Skipped Description Step")

	bot.send_message(update.message.chat_id,
					text = ethumbs + "Description was skipped.\n" +
					"\nThe next step is assign some tags so people could search the sound more easily.\n\n" +
					"Please write 1 to 5 tags separated by comma.\n\n" +
					"Example: dog, barking, animals, cute" +
					"\n\nIf you want to skip this step write /skip\n"
					)

	return TAGS_STATE

def tags_step(bot, update):
	user = update.message.from_user
	
	logger.info("User %s will set the tags for the new sound." % user.username)

	voice = voiceForUser(user.username)

	tags = update.message.text

	if tags == None:
		tags = ""
	
	# Clean white space in every tag
	# and create an array of items
	tags = [x.strip() for x in tags.split(',')]

	# Truncate long tags
	for i, tag in enumerate(tags):
		tags[i] = tag[:120]

	logger.debug("Tags Given %s" % tags)


	if len(tags) < 1:
		logger.info("User typed not enough tags")

		bot.send_message(update.message.chat_id,
			text = ewarning + "Too few tags\n" +
			"\nPlease write 1 to 5 tags separated by comma.\n\n" +
			"Example: dog, barking, animals, cute" +
			"\n\nIf you want to skip this step write\n/skip\n"
			)

		return TAGS_STATE

	if len(tags) > 5:
		logger.info("User typed a lot of tags")

		bot.send_message(update.message.chat_id,
			text = ewarning + "There are more than 5 tags\n" +
			"\nYour tags were %s\n" % update.message.text +
			"\nPlease write 1 to 5 tags separated by comma.\n\n" +
			"Example: dog, barking, animals, cute" +
			"\n\nIf you want to skip this step write\n/skip\n"
			)

		return TAGS_STATE

	# Convert the array to string again
	voice.tags = ",".join(tags)

	logger.info("Voice object changed tags %s" % voice)

	logger.info("All validations were ok.")
	bot.send_message(update.message.chat_id,
					text = ethumbs + " Yay!, we just need the voice now\n" +
					"\nPlease record a sound with your mic or foward me a voice message\n" +
					emic
					)

	return UPLOAD_STATE

def skip_tags_step(bot, update):
	
	logger.info("Skipped Tags Step")

	bot.send_message(update.message.chat_id,
					text = ethumbs + " No tags? OK!, we just need the voice now\n" +
					"\nPlease record a sound with your mic or foward me a voice message\n" +
					emic
					)

	return UPLOAD_STATE


def upload_step(bot, update):

	user = update.message.from_user
	
	logger.info("User %s will set the voice file for the new sound." % user.username)


	upload = update.message.voice


	if upload == None or \
	not (upload.mime_type == "audio/ogg" or \
	upload.mime_type == "audio/mpeg"):
		
		logger.warn("Wrong File Uploaded %s" % upload.mime_type)

		bot.send_message(update.message.chat_id,
			text = ewarning + "The file uploaded is not a voice message\n"
			"\nPlease record a sound with your mic or foward me a voice message\n" +
					emic)

		return UPLOAD_STATE

	voice = voiceForUser(user.username)

	voice.file_id = upload.file_id

	resetRetriesForUser(user.username)

	return uploadVoiceFile(bot, update)

def retry_upload_step(bot, update):

	logger.info("Upload failed, trying again")

	user = update.message.from_user

	retry_count = getRetriesForUser(user.username)

	bot.send_message(update.message.chat_id,
		text = "\nUpload failed, trying again. Retry #(%s) of #(%s)\n\n" % (str(retry_count), str(max_retries)) + 
		"You can /cancel the upload or \n/change the voice.\n")


	if retry_count >= max_retries:
		
		logger.info("Max Retries Reached. Stop Uploading.")

		bot.send_message(update.message.chat_id, 
				ewarning + "There was a problem uploading the file.\n" +
				"\nYou reached the max number of retries (%s)." % str(max_retries) +
				"\n\nPlease try again later.\n" +
				"\nNew Sound Creation Aborted.\n"
				)

		resetRetriesForUser(user.username)
		
		return ConversationHandler.END

	setRetriesForUser(user.username, retry_count + 1)

	return uploadVoiceFile(bot, update)


def uploadVoiceFile(bot, update):

	user = update.message.from_user

	voice = voiceForUser(user.username)

	logger.info("Voice file complete %s\n Prepare to upload file to the server", voice)


	bot.send_message(update.message.chat_id,
		text = "Saving sound \n" + 
		"\nTitle: %s \nEmoji: %s \nTags: %s\nPublic: %s\n\n" % 
		(voice.title, voice.description, voice.tags, str(voice.public)) +
		"in the database... Please wait... %s\n" % erocket
		)

	success = False

	params = voice.vars()

	try:
		
		logger.info("Calling Endpoint %s with params %s and auth user %s pass %s" % (config.voices, 
			params, config.user, config.password))

		response = requests.post(config.voices, data=params, auth=config.auth)
		
		logger.info("Got Response")

		logger.debug(response.text)

		if response.ok and response.status_code == 201:
			success = True
		else:
			
			if response.status_code == 200:
				logger.info("Wrong status code given")
				raise Exception("Wrong Status Code")

			data = response.json()

			if data['error']['number'] == 2001:

				logger.info("Title Conflict. Should Enter Title Again.")

				bot.send_message(update.message.chat_id, 
				ewarning + "There was a problem uploading the file.\n" +
				"\nThe title '%s' is already in use" % voice.title +
				"\n\nPlease write a new title")

				return TITLE_AGAIN_STATE

			if data['error']['number'] == 2002:

				logger.info("Emoji Conflict. Should Enter Emoji Again.")

				bot.send_message(update.message.chat_id, 
				ewarning + "There was a problem uploading the file.\n" +
				"\nThe emoji '%s' is already in use" % voice.description +
				"\n\nPlease write a new emoji.")

				return DESCRIPTION_AGAIN_STATE

			if data['error']['number'] == 2003:

				logger.info("Max Voices Reached. Should Delete One.")

				bot.send_message(update.message.chat_id, 
				ewarning + "There was a problem uploading the file.\n" +
				"\nYou reached the max number of files (%s) for storing." % str(data['_meta']['max_items']) +
				"\n\nPlease /delete one and\n /retry again later.\n" +
				"\nNew Sound Creation Aborted.\n"
				)

				return ConversationHandler.END

			if data['error']['number'] == 2004:

				logger.info("Tried to upload the same file id twice.")

				
				bot.send_message(update.message.chat_id, 
				ewarning + "There was a problem uploading the file.\n" +
				"\nThe same file id (%s)\n" % str(data['_meta']['conflict_file_id']) +
				"\nWas found for the emoji (%s).\n" % str(data['_meta']['conflict_page']['emoji']) +
				"\nPlease upload a different voice file. " + emic + 
				"\n"
				)

				return UPLOAD_STATE

	except Exception as e:

		logger.info("Exception Throwed")
		logger.debug(e)

		bot.send_message(update.message.chat_id, 
			ewarning + "There was a problem uploading the file\nPlease /retry again")

		return RETRY_UPLOAD_STATE

	if success:

		voice = voiceForUser(user.username)

		resetRetriesForUser(user.username)

		bot.send_message(update.message.chat_id, 
			"Jobs Done!, Your sound is ready to be shared\n" +
			eparty + econfetti + eparty + econfetti + eparty + econfetti +
			"\n\nUse @voxgrambot %s for sending the sound.\n" % voice.description)

		return ConversationHandler.END

	else:
		
		bot.send_message(update.message.chat_id, 
			ewarning + "There was a problem uploading the file\nPlease /retry again")

		return RETRY_UPLOAD_STATE


def cancel(bot, update):
	user = update.message.from_user
	
	logger.info("User %s canceled the new sound conversation." % user.username)
	
	bot.send_message(update.message.chat_id,
					text = emoai + "New Sound Creation Aborted. Ok no problemo, maybe later \n" +
					esmile +
					"\nIf you need help just type /help"
					)

	return ConversationHandler.END

def stats(bot, update):

	if not is_private_chat(bot, update):
		return ConversationHandler.END

	user = update.message.from_user

	logger.info("User %s wants to know its stats." % user.username)

	args = update.message.text.split()

	if len(args) > 1:
		logger.info("Param used %s" % args[1])

	endpoint = config.voices + user.username + '/'

	params = {}

	response = requests.get(endpoint, data=params, auth=config.auth)
		
	logger.info("Got Response")

	logger.debug(response.text)

	if response.ok and response.status_code == 200:
		logger.debug("OK Response")
		
		data = response.json()

		userData = data['data']['user']
		voices = userData['voices']

		bot.send_message(update.message.chat_id,
					text = emoai + " S T A T S " + emoai +
					"\nThese are your stats\n\n" +
					"Total Voice Message Saved: %s\n" % str(voices['quantity']) +
					"Max Voice Messages: %s\n" % str(voices['max']) +
					"Available Voice Messages: %s\n" % str(voices['available']) +
					"Emojis Used: %s\n" % userData['usedEmojis'] +
					"\nIf you want to hear a sound type /hear <emoji>\n" +
					"If you want to delete a sound type /delete <emoji>\n" +
					"\nwhere <emoji> is the emoji associated with the sound.\n" +
					"\nAlso you can use /help for more info.\n"
					)



def hear(bot, update):

	if not is_private_chat(bot, update):
		return ConversationHandler.END

	try:
		user = update.message.from_user

		args = update.message.text.split()

		param = ''
		query = '<empty>'

		if len(args) > 1:
			logger.info("Param used %s" % args[1])
			param = args[1].strip()
		else:
			raise Exception("No Params Used")

		logger.info("User %s wants to play %s." % (user.username, param))


		# Example Response
		#no_homo = VoiceFile(title = "No Homo", file_id = "AwADAQADEgAD2qz9Db1R-agaK9zjAg")
		#logger.debug(no_homo)
		#results.append(no_homo.voice())

		query = param

		endpoint = config.voices + "?query=%s&username=%s" % (query, user.username)
		
		params = {"query" : query,
				  "username" : user.username
				 }

		response = requests.get(endpoint, data=params, auth=config.auth)

		logger.debug("Calling Endpoint %s Params %s URL %s" % (endpoint, params, response.url))
		
		logger.info("Got Response")

		logger.debug(response.text)

		results = list()

		if response.ok and response.status_code == 200:

			logger.debug("OK Response")
			
			data = response.json()
			data = data["data"]

			for voice_data in data:
				
				caption = "%s - %s" % (voice_data["emoji"], voice_data["tags"])

				if voice_data["emoji"] == query:

					voice = VoiceFile(title = voice_data["title"], tags=voice_data["tags"], file_id = voice_data["file_id"], caption=caption, emoji=voice_data["emoji"], public=voice_data["public"])

					logger.debug("Voice Result %s" % str(voice))

					results.append(voice)

			logger.debug("Results %s" % results)

			if len(results) > 0:

				voice = results[0]

				bot.send_message(update.message.chat_id, 
					text = estar + " Here's the sound for the emoji %s\n" % voice.emoji +
					"Title: %s\n" % voice.title +
					"Tags: %s\n" % voice.tags +
					"Emoji: %s\n" % voice.emoji +
					"Public Access: %s\n" % voice.public +
					"Know your emojis in /stats\n"
					)

				bot.send_voice(update.message.chat_id, voice=voice.file_id)

				bot.send_message(update.message.chat_id, text= "\nYou can use /delete %s\n" % voice.emoji)

			else:
				raise Exception("No Results Found")
		
		else:
			raise Exception("No Results Found")

	except Exception as e:
		logger.warn(e)
		bot.send_message(update.message.chat_id,
					text = "Sorry no sounds found for " + query +
					"\nTry another emoji " + ewink +
					"available in /stats" + estar +
					"\n"
					)

def delete(bot, update):

	if not is_private_chat(bot, update):
		return ConversationHandler.END

	try:
		user = update.message.from_user

		args = update.message.text.split()

		param = ''
		query = '<empty>'

		if len(args) > 1:
			logger.info("Param used %s" % args[1])
			param = args[1]
		else:
			raise Exception("No Params Used")

		logger.info("User %s wants to delete %s." % (user.username, param))


		# Example Response
		#no_homo = VoiceFile(title = "No Homo", file_id = "AwADAQADEgAD2qz9Db1R-agaK9zjAg")
		#logger.debug(no_homo)
		#results.append(no_homo.voice())

		query = param

		endpoint = config.voices + "?query=%s&username=%s" % (query, user.username)
		
		params = {"query" : query,
				  "username" : user.username
				 }

		response = requests.get(endpoint, data=params, auth=config.auth)

		logger.debug("Calling Endpoint %s Params %s URL %s" % (endpoint, params, response.url))
		
		logger.info("Got Response")

		logger.debug(response.text)

		results = list()

		if response.ok and response.status_code == 200:

			logger.debug("OK Response")
			
			data = response.json()
			data = data["data"]

			for voice_data in data:

				if voice_data["emoji"] == query:

					voice = VoiceFile(title = voice_data["title"], 
						tags=voice_data["tags"], 
						file_id = voice_data["file_id"], 
						emoji=voice_data["emoji"], 
						public=voice_data["public"], 
						url=voice_data["_href"]["self"])

					logger.debug("Voice Result %s" % str(voice))

					results.append(voice)

			logger.debug("Results %s" % results)

			if len(results) > 0:

				voice = results[0]

				endpoint = voice.url

				logger.debug("Calling Endpoint %s Params %s" % (endpoint, params))

				response = requests.delete(endpoint, json=params, auth=config.auth)
				logger.debug(response.text)

				if response.status_code == 202:
					bot.send_message(update.message.chat_id, text= emoai + emoai + emoai + "\nV O I C E  D E L E T E D\n" +
						"You can use /stats for more info\n" + emoai + emoai + emoai)
				else:
					bot.send_message(update.message.chat_id, text="I could not delete the sound you requested. I'm sorry " + eskull +
						" Please try again later.")
			else:
				raise Exception("No Results Found")
		
		else:
			raise Exception("No Results Found")

	except Exception as e:
		logger.warn(e)
		bot.send_message(update.message.chat_id,
					text = "Sorry no sounds found for " + query +
					"\nTry another emoji " + ewink +
					"available in /stats" + estar +
					"\n"
					)

def about(bot, update):
	bot.send_message(update.message.chat_id,
		text = emoai + " V O X G R A M  B O T " + emoai +
		"\n\nI was created in Chile " + echile + 
		" By Camilo Castro (twitter:camcasc)\n\n" +
		"Using Python 3.x with Telegram Bot Framework (https://python-telegram-bot.org)\n" +
		"And ProcessWire (https://www.processwire.com) for the Backend.\n" +
		"\nCoded with a lot of love\n" +
		eheart + eheart + eheart)

# Main Loop
def main():
	
	logger.info("Initializing Voxgram Bot")

	updater = Updater(config.telegram_key)
	
	dp = updater.dispatcher

	dp.add_handler(InlineQueryHandler(inlinequery))

	new_sound_handler = ConversationHandler(
			
			entry_points = [CommandHandler("new", new_sound),
							CommandHandler("add", new_sound)],

			states = {

				PRIVACY_SELECTION_STATE: [CommandHandler('private', private_chosen_step),
								CommandHandler('public', public_chosen_step)],

				TITLE_STATE: [MessageHandler([Filters.text], title_step)],

				TITLE_AGAIN_STATE: [MessageHandler([Filters.text], title_again_step)],

				DESCRIPTION_STATE: [MessageHandler([Filters.text], description_step),
									# CommandHandler('skip', skip_description_step)
									],

				DESCRIPTION_AGAIN_STATE: [MessageHandler([Filters.text], description_again_step)],

				TAGS_STATE: [MessageHandler([Filters.text], tags_step),
									CommandHandler('skip', skip_tags_step)],

				UPLOAD_STATE: [MessageHandler([Filters.voice], upload_step)],

				RETRY_UPLOAD_STATE: [MessageHandler([Filters.text], retry_upload_step),
									CommandHandler('change', upload_step),
									CommandHandler('cancel', cancel),
									CommandHandler('retry', retry_upload_step)]
			},

			fallbacks=[CommandHandler("cancel", cancel)]
		)

	dp.add_handler(new_sound_handler)

	dp.add_handler(CommandHandler('stats', stats))
	dp.add_handler(CommandHandler('stat', stats))

	dp.add_handler(CommandHandler('hear', hear))
	dp.add_handler(CommandHandler('delete', delete))

	dp.add_handler(CommandHandler('about', about))
	# Help
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('hi', help))
	dp.add_handler(CommandHandler('hello', help))
	dp.add_handler(CommandHandler('start', help))

	# Match any other string with the help
	#dp.add_handler(RegexHandler("[\s\S]*?", help))
	dp.add_handler(RegexHandler("(?i)(hi)", help))
	dp.add_handler(RegexHandler("(?i)(help)", help))
	dp.add_handler(RegexHandler("(?i)(hello)", help))
	dp.add_handler(RegexHandler("(?i)(start)", help))
	dp.add_handler(RegexHandler("(?i)(hola)", help))

	dp.add_error_handler(error)

	logger.info("Started Listening Updates")
	updater.start_polling()

	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()

if __name__ == '__main__':
	main()

	transaction.commit()
	db.close()
	connection.close()
	
	logger.info("Voxgram Terminated")
