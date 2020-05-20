import sys
import os
import time
import requests
import json
import re
import random

# petit module de constantes, de bon aloi
import constantes

# les dicts qui sont transformés en JSON pour poster des résultats vers TG
senddoc = { "chat_id":"0", "document":"", "reply_to_message_id":"0" }
sendphoto = { "chat_id":"0", "photo":"", "reply_to_message_id":"0" }
sendmessage = { "chat_id":"0", "text":"", "reply_to_message_id":"0" }

# le transformé en JSON pour emettre une demande de réception de mise à jour
getupdates = { 	"offset":"0", "timeout":"100", "allowed_updates": [ "messages", "channel_post" ] }

# Fonction de chargement/re-chargement des fichiers de définition
def reload_files():
	print ("(re-)chargement du mapping des emoticons")
	constantes.emoticons = {}
	f = open(constantes.emoticons_file,"r")
	constantes.emoticons = json.loads(f.read())

	print ("(re-)chargement du mapping des regex")
	constantes.regex_tab = {}
	f = open(constantes.regex_file,"r")
	constantes.regex_tab = json.loads(f.read())

	print ("(re-)chargement des films pouic")
	constantes.films_tab.clear()
	f = open(constantes.films_file,"r")
	for film in f:
		constantes.films_tab.append(film)

# Renvoi des émoticons
def try_to_send_emoticon(code, chat_id, msg_id):
	if code in constantes.emoticons:
		emoticon_file = constantes.emoticons[code]
		emoticon_url = constantes.url_gif + emoticon_file
		print("match ! tentative d'envoi : " + emoticon_url)

		if emoticon_file[len(emoticon_file)-3:len(emoticon_file)] == "jpg":
			# Jpeg ...
			sendphoto['photo'] = emoticon_url
			sendphoto['chat_id'] = chat_id
			sendphoto['reply_to_message_id'] = msg_id
			result = requests.post(constantes.base_url + "/sendPhoto", json = sendphoto)
		elif emoticon_file[len(emoticon_file)-3:len(emoticon_file)] == "png":
			# PNG ...
			sendphoto['photo'] = emoticon_url
			sendphoto['chat_id'] = chat_id
			sendphoto['reply_to_message_id'] = msg_id
			result = requests.post(constantes.base_url + "/sendPhoto", json = sendphoto)
		else:
			# GIF, entre autres ...
			senddoc['document'] = emoticon_url
			senddoc['chat_id'] = chat_id
			senddoc['reply_to_message_id'] = msg_id
			result = requests.post(constantes.base_url + "/sendDocument", json = senddoc)

		retour = result.json()
		if retour.get('ok'): print('sent')
		else:
			print("error:")
			print(retour)
	else: print("no match.")

# Renvois d'un message generique
def try_to_send_message(texte,chat_id,msg_id):
	sendmessage['text'] = texte
	sendmessage['chat_id'] = chat_id
	sendmessage['reply_to_message_id'] = msg_id
	print("tentative d'envoi de message : " + sendmessage['text'])
	result = requests.post(constantes.base_url + "/sendMessage", json = sendmessage)
	retour = result.json()
	if retour.get('ok'): print('sent')
	else:
		print("error:")
		print(retour)

# Test des regex/chaines
def try_to_send_pouic_message(chat_id,msg_id):
	idx=random.randrange(1,len(constantes.films_tab))
	try_to_send_message(constantes.films_tab[idx],chat_id,msg_id)

# Test des regex/chaines
def test_the_matches_and_send(text_to_match,chat_id,msg_id):
	dice = random.randrange(1,3)
	if (dice == 1):
		print("calme ... tirage", end='')
		print(dice)
	else:
		for match in constantes.regex_tab:
#			print("debug: trying to find >" + match + "< -> " + constantes.regex_tab[match])
			if re.search(match, text_to_match):
				print("debug: match ! " + constantes.regex_tab[match])
				try_to_send_message(constantes.regex_tab[match],chat_id,msg_id)
				break

### MAIN LOOP ###
reload_files()
print ("lancement de la boucle infinie de reception des updates ...")
offset=0
while True :
	getupdates['offset'] = offset
	print("attente updates ...")
	result = requests.post(constantes.base_url + "/getUpdates",data=getupdates)
	retour = result.json()
	
	if not retour['ok']:
		print("retour en erreur. stop")
		print(json.dumps(retour))
		break
	else:
		update_list = retour.get('result')
		for update_message in update_list:
			print("/!\ incoming update /!\ ")
			print("update_id: ", end="")
			print(update_message['update_id'])
			offset=int(update_message['update_id']) + 1

			if ('message' in update_message):
				print(json.dumps(update_message))
				the_message=update_message['message']
				if 'text' in the_message:
					the_text=the_message['text']
					the_chat=the_message['chat']

# D'abord les fondamentaux (commandes, réparties, émoticons)
					if (the_text == "/reload_files"): reload_files()
					elif (the_text[0:1] == ":" ): try_to_send_emoticon(the_text.lower(), the_chat['id'], "0")
					elif (the_text[0:5].lower() == "pouic" ): try_to_send_pouic_message(the_chat['id'], the_message['message_id'])
# Et enfin les regex
					else: test_the_matches_and_send(the_text.lower(), the_chat['id'], the_message['message_id'])
				else:
					print("message sans texte, ignore")
			elif ('edited_message' in update_message):
					print("edited_message, ignore")
			elif ('inline_query' in update_message):
					print("inline_query, ignore ... pour le moment ^^")
			else:
				print("reception d'un type d'update inconnu, skip")
			# end main if
		# end for
	# end boucle infinie, while true

