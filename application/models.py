"""
	models.py

	Model descriptions for passbank.

	This software is licensed under the Draconic
	Free License version 1. Please refer to LICENSE.txt
	for more information.
"""

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, BLOB, ForeignKey

Base = declarative_base()

class Account(Base):
	""" Account entries. """
	__tablename__ = 'account'

	id = Column(Integer, primary_key=True)
	name = Column(String(256))
	ciphertext = Column(BLOB(256))
	iv = Column(BLOB(256))
	folder = Column(Integer, ForeignKey('folder.id'))

	def __init__(self, name, password, upper_password):
		self.name = name

		iv = Random.new().read(AES.block_size)
		key = PBKDF2(upper_password, iv, 16, 9000)
		cipher = AES.new(key, AES.MODE_CFB, iv)

		self.iv = iv
		self.ciphertext = cipher.encrypt(key + 'DRAGONS' + password)

	def get_plain(self, password):
		iv = self.iv
		key = PBKDF2(password, iv, 16, 9000)
		cipher = AES.new(key, AES.MODE_CFB, iv)
		decrypted = cipher.decrypt(self.ciphertext).split('DRAGONS')
		# Verify that we are actually correct
		if (len(decrypted) != 2 or decrypted[0] != key):
			return None
		else:
			return decrypted[1]

class Folder(Base):
	""" Account containers for organization. """
	__tablename__ = 'folder'

	id = Column(Integer, primary_key=True)
	name = Column(String(256))
	accounts = relationship('Account')

	def __init__(self, name):
		self.name = name
