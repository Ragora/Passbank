"""
	main.py

	Main source file for the passbank application.

	Copyright (c) 2013 Robert MacGregor
"""

import sys
import getpass

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import scoped_session, sessionmaker

import models

PAGE_MAIN = 0
PAGE_INPUT_NAME = 1
PAGE_INPUT_PASSWORD = 2
PAGE_INPUT_KEY = 3
PAGE_INPUT_VERIFY_KEY = 4
PAGE_VIEW_FOLDERS = 5
PAGE_VIEW_ACCOUNTS = 6
PAGE_SELECT_FOLDER = 7
PAGE_VIEW_FOLDER = 8
PAGE_CREATE_FOLDER = 9
PAGE_SELECT_ACCOUNT = 10
PAGE_QUERY_ACCOUNT = 11
PAGE_DECODE_PASSWORD = 12

QUERY_PASSWORD = 0
QUERY_NORMAL = 1
APPLICATION_END = -1


class Application:
	database_engine = None
	page = PAGE_MAIN

	account_lower_password = None
	account_upper_password = None
	account_folder_name = None
	account_folder = None
	account_name = None
	selected_folder = None
	selected_account = None
	

	def main(self):
		print('PassBank')
		print('Copyright (c) 2013 Robert MacGregor')

		self.database_engine = create_engine('sqlite:///database.db', echo=False)
		self.connection = self.database_engine.connect()
		models.Base.metadata.create_all(self.database_engine)

		self.print_actions()
		result = QUERY_NORMAL
		while (True):
			if (result == QUERY_NORMAL):
				input = raw_input('Input: ')
			else:
				input = getpass.getpass()

			result = self.process_action(input)

			print(' ')
			if (result == APPLICATION_END):
				break

	def print_actions(self):
		print('What would you like to do?')
		print('0.) Exit')
		print('1.) Look up Entries')
		print('2.) Create an Entry')

	def process_action(self, input):
		input_integer = -1
		try:
			input_integer = int(input)
		except ValueError:
			input_integer = -1

		if (input == ''):
			print('Cancelled.')
			self.account_lower_password = None
			self.account_upper_password = None
			self.account_folder_name = None
			self.account_name = None
			self.selected_folder = None
			self.selected_account = None
			self.page = PAGE_MAIN
			self.print_actions()
			return QUERY_NORMAL

		if (self.page == PAGE_MAIN):
			if (input_integer == 0):
				return APPLICATION_END
			elif (input_integer == 1):
				session = scoped_session(sessionmaker(bind=self.database_engine))
				folders = session.query(models.Folder)

				if (folders.count() == 0):
					print('There are no folders.')
					self.print_actions()
					return 1
				else:
					print('0.) Exit')
					self.page = PAGE_VIEW_FOLDERS
					for index, folder in enumerate(folders):
						print('%u.) %s' % (index + 1, folder.name))

				self.page = PAGE_VIEW_FOLDERS
				return QUERY_NORMAL
			elif (input_integer == 2):
				print('Please type in a name: ')
				self.page = PAGE_INPUT_NAME
				return QUERY_NORMAL
		elif (self.page == PAGE_VIEW_FOLDERS and input_integer == 0):
			self.page = PAGE_MAIN
			self.print_actions()
			return QUERY_NORMAL
		elif (self.page == PAGE_VIEW_FOLDERS):
			input_integer -= 1
			session = scoped_session(sessionmaker(bind=self.database_engine))
			folders = session.query(models.Folder)

			try:
				folder = folders[input_integer]
			except IndexError:
				print('Invalid folder.')
				self.page = PAGE_MAIN
				self.print_actions()
				return QUERY_NORMAL

			folder = folders[input_integer]
			print('0.) Back')
			for index, account in enumerate(folder.accounts):
				print('%u.) %s' % (index + 1, account.name))
			self.selected_folder = folder.id

			self.page = PAGE_SELECT_ACCOUNT
			return QUERY_NORMAL
		elif (self.page == PAGE_SELECT_ACCOUNT and input_integer == 0):
			self.page = PAGE_MAIN
			self.print_actions()
			return QUERY_NORMAL
		elif (self.page == PAGE_SELECT_ACCOUNT):
			input_integer = input_integer - 1

			session = scoped_session(sessionmaker(bind=self.database_engine))
			folder = session.query(models.Folder).filter_by(id=self.selected_folder).first()
			if (len(folder.accounts)-1 < input_integer or input_integer < 0):
				print('Invalid account.')
				return QUERY_NORMAL

			account = folder.accounts[input_integer]
			print(account.name)
			print('0.) Back')
			print('1.) View Password')
			print('2.) Delete Entry')

			self.selected_account = input_integer
			self.page = PAGE_QUERY_ACCOUNT

			return QUERY_NORMAL
		# Account specific controls
		elif (self.page == PAGE_QUERY_ACCOUNT):
			session = scoped_session(sessionmaker(bind=self.database_engine))
			folder = session.query(models.Folder).filter_by(id=self.selected_folder).first()

			if (input_integer == 2):
				print('Done.')

				session.delete(folder.accounts[self.selected_account])
				folder.accounts.pop(self.selected_account)
				if (len(folder.accounts) == 0):
					session.delete(folder)
				session.commit()
			elif (input_integer == 1):
				print('Please enter the key this account was encrypted with: ')
				self.page = PAGE_DECODE_PASSWORD
				return QUERY_PASSWORD

			self.page = PAGE_MAIN
			self.print_actions()
			return QUERY_NORMAL
		elif (self.page == PAGE_DECODE_PASSWORD):
			self.page = PAGE_MAIN

			session = scoped_session(sessionmaker(bind=self.database_engine))
			folder = session.query(models.Folder).filter_by(id=self.selected_folder).first()
			account = folder.accounts[self.selected_account]

			plain = account.get_plain(input)
			if (plain is None):
				print('Invalid key.')
				return QUERY_PASSWORD
			else:
				print('Out: ' + plain)
			print(' ')
			self.print_actions()
			return QUERY_NORMAL
		# Password Entry System
		elif (self.page == PAGE_INPUT_NAME):
			print('Please Select a folder: ')
			self.account_name = input

			session = scoped_session(sessionmaker(bind=self.database_engine))
			folders = session.query(models.Folder)

			print('0.) Create a New Folder')
			for index, folder in enumerate(folders):
				print('%u.) %s' % (index + 1, folder.name))
			
			self.page = PAGE_SELECT_FOLDER
			return QUERY_NORMAL
		elif (self.page == PAGE_SELECT_FOLDER and input_integer == 0):
			print('Please Type Folder Name: ')
			self.page = PAGE_CREATE_FOLDER
			return QUERY_NORMAL
		elif (self.page == PAGE_SELECT_FOLDER):
			input_integer = input_integer - 1
			session = scoped_session(sessionmaker(bind=self.database_engine))
			folders = session.query(models.Folder)

			try:
				folder = folders[input_integer]
			except IndexError:
				print('Invalid folder.')
				return QUERY_NORMAL

			if (folder is None):
				print('Invalid folder.')
				return QUERY_NORMAL

			print('Please Type the Password to be Stored: ')
			self.account_folder = folder.id
			self.page = PAGE_INPUT_PASSWORD
			return QUERY_NORMAL
		elif (self.page == PAGE_CREATE_FOLDER):
			print('Please Type the Password to be Stored: ')
			self.account_folder_name = input
			self.page = PAGE_INPUT_PASSWORD
			return QUERY_NORMAL
		elif (self.page == PAGE_INPUT_PASSWORD):
			print('Please Type the key to Encrypt With: ')
			self.account_lower_password = input
			self.page = PAGE_INPUT_KEY
			return QUERY_PASSWORD
		elif (self.page == PAGE_INPUT_KEY):
			print('Please Verify: ')
			self.account_upper_password = input
			self.page = PAGE_INPUT_VERIFY_KEY
			return QUERY_PASSWORD
		elif (self.page == PAGE_INPUT_VERIFY_KEY and input != self.account_upper_password):
			print('Mismatching keys. Try again: ')
			self.page = PAGE_INPUT_KEY
			return QUERY_PASSWORD
		elif (self.page == PAGE_INPUT_VERIFY_KEY):
			print('Entry created.')
			self.page = PAGE_MAIN

			session = scoped_session(sessionmaker(bind=self.database_engine))
			account = models.Account(self.account_name, self.account_lower_password, self.account_upper_password)

			folder = None
			if (self.account_folder_name is not None):
				folder = models.Folder(self.account_folder_name)
			else:
				folder = session.query(models.Folder).filter_by(id=self.account_folder).first()

			folder.accounts.append(account)
			session.add(folder)
			session.add(account)
			session.commit()
			
			self.account_lower_password = None
			self.account_upper_password = None
			self.account_folder_name = None
			self.account_folder = None
			self.account_name = None

			self.print_actions()
			return QUERY_NORMAL


if __name__ == '__main__':
	app = Application()
	app.main()
