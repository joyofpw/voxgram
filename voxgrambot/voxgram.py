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

import logging

import requests

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
echile = u'\U0001F1E8'
eskull = u'\U0001F480'
erocket = u'\U0001F680'
estar = u'\U0001F31F'
esparkles = u'\U00002728'
eparty = u'\U0001F389'
econfetti = u'\U0001F38A'

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

# create a map if needed
if not "voices" in root:
	root["voices"] = {}

voices = root["voices"]

transaction.commit()

logger.info("DataBase Initialized")

# Data Base Functions
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

def escape_markdown(text):
    """Helper function to escape telegram markup symbols"""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def help(bot, update):
	logger.info("Sending the Start Message")
	bot.send_message(update.message.chat_id, 
					text="Howdy!, I'm VoxGram Bot. " + ewink +
					"\nI store voice messages so you can send them " +
					"to your friends!.\n"  +
					"\nIf you want to search a voice message, " +
					"just type \n\n@voxgrambot <query>\n\n in a group chat.\n" +
					"\nIf you want to add a new sound start a private\n" +
					"conversation with me and type /new."
					)

def inlinequery(bot, update):
	query = update.inline_query.query
	results = list()

	no_homo = VoiceFile(title = "No Homo", file_id = "AwADAQADEgAD2qz9Db1R-agaK9zjAg")

	logger.debug(no_homo)

	results.append(no_homo.voice())

	bot.answerInlineQuery(update.inline_query.id, results=results)

# The Process for Deleting a Sound
def delete_sound(bot, update):
	pass 

# The Process for Creating a New Sound
TITLE_STATE, DESCRIPTION_STATE, TAGS_STATE, UPLOAD_STATE = range(4)

def new_sound(bot, update):
	user = update.message.from_user
	
	logger.info("User %s started new sound conversation." % user.username)

	if update.message.chat.type == 'private':

		bot.send_message(update.message.chat_id,
						text="Ok, before adding a new voice message\n"
						"I need some basic info.\n\n"
						"If you want to stop creating a new sound\n"
						"just type /cancel \n"
						"\nFirst I need the title for the sound\n\n"
						"Please write a title with 50 characters or less.\n"
						)

		deleteVoiceForUser(user.username)

		return TITLE_STATE

	else:
	
		logger.info("Chat is not private")
	
		bot.send_message(update.message.chat_id,
						text = "Sorry, but for creating a new sound you need to send me a private message. " + emoai
						)
	
		return ConversationHandler.END


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
					"\nNow we need a description so people will know what the sound is about.\n\n" +
					"Please tell me about the audio. 50 characters or less.\n"
					"\nIf you want to skip this step write /skip\n"
					)

	return DESCRIPTION_STATE

def description_step(bot, update):
	user = update.message.from_user
	
	logger.info("User %s will set the description for the new sound." % user.username)

	voice = voiceForUser(user.username)

	description = update.message.text

	if description == None:
		description = ""

	logger.debug("Description Given %s" % description)
	
	description = description.strip()

	if len(description) < 1:
		logger.info("User typed a too short description")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The description is too short.\n" +
			"Please write a description with at least 1 non whitespace character.\n" +
			"\nIf you want to skip this step write /skip\n"
			)

		return DESCRIPTION_STATE

	if len(description) > 50:
		logger.info("User typed a long description")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The description is too long.\n" +
			"Please write a description that contains 50 characters or less.\n" +
			"\nIf you want to skip this step write /skip\n"
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
					"\n\nIf you want to skip this step write /skip\n"
					)

	return TAGS_STATE

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
			"\n\nIf you want to skip this step write /skip\n"
			)

		return TAGS_STATE

	if len(tags) > 5:
		logger.info("User typed a lot of tags")

		bot.send_message(update.message.chat_id,
			text = ewarning + "There are more than 5 tags\n" +
			"\nYour tags were %s\n" % update.message.text +
			"\nPlease write 1 to 5 tags separated by comma.\n\n" +
			"Example: dog, barking, animals, cute" +
			"\n\nIf you want to skip this step write /skip\n"
			)

		return TAGS_STATE

	voice.tags = tags
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

	voice = voiceForUser(user.username)

	upload = update.message.voice

	if upload == None or upload.mime_type != "audio/ogg":
		
		logger.warn("Wrong File Uploaded")

		bot.send_message(update.message.chat_id,
			text = ewarning + "The file uploaded is not a voice message\n"
			"\nPlease record a sound with your mic or foward me a voice message\n" +
					emic)

		return UPLOAD_STATE

	voice.file_id = upload.file_id

	logger.info("Voice file complete %s\n Prepare to upload file to the server", voice)


	bot.send_message(update.message.chat_id,
		text = "Saving sound \n" + 
		"\nTitle: %s \nDescription: %s \nTags: %s \n\n" % (voice.title, voice.description, voice.tags) +
		"in the database... Please wait... %s\n" % erocket
		)

	success = False


	return ConversationHandler.END

def cancel(bot, update):
	user = update.message.from_user
	
	logger.info("User %s canceled the new sound conversation." % user.username)
	
	bot.send_message(update.message.chat_id,
					text = emoai + "New Sound Creation Aborted. Ok no problemo, maybe later \n" +
					esmile +
					"\nIf you need help just type /help"
					)

	return ConversationHandler.END

# Main Loop
def main():
	
	logger.info("Initializing Voxgram Bot")

	updater = Updater("234728666:AAFIZxSY_TRUHmsFUKyJgySxfSZhFXzCkaU")
	
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("start", help))
	dp.add_handler(CommandHandler("help", help))
	dp.add_handler(InlineQueryHandler(inlinequery))

	new_sound_handler = ConversationHandler(
			entry_points=[CommandHandler("new", new_sound)],
			states = {
				TITLE_STATE: [MessageHandler([Filters.text], title_step)],

				DESCRIPTION_STATE: [MessageHandler([Filters.text], description_step),
									CommandHandler('skip', skip_description_step)],

				TAGS_STATE: [MessageHandler([Filters.text], tags_step),
									CommandHandler('skip', skip_tags_step)],

				UPLOAD_STATE: [MessageHandler([Filters.voice], upload_step)]
			},
			fallbacks=[CommandHandler("cancel", cancel)]
		)

	dp.add_handler(new_sound_handler)

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
