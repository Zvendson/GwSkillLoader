import os
import threading
import requests
import shutil

_URL = 'https://gwpvx.fandom.com/extensions-ucp/PvXCode/images/img_skills/{}.jpg'


class SkillDownloader(object):

	def __init__(self, max_skills: int, path: str, skip_existing: bool = True, workers: int = 10):
		self._downloads = 0
		self._passed = 0
		self.skip = skip_existing
		self.max = max_skills
		self.path = path
		self.workers = workers

		if not os.path.exists(path):
			os.makedirs(path)

		self.threads = dict()
		self.threads_downloads = dict()
		self._lock = threading.Lock()
		self._passlock = threading.Lock()
		self._skilllock = threading.Lock()

		self._skills = list()
		self._queued = 0

	def change_path(self, target: str):
		self.path = target
		self._skills.clear()

		for skillid in range(self.max):
			if self.skip and os.path.exists(f'{self.path}/{skillid}.jpg'):
				continue

			self._skills.append(skillid)

		self._queued = len(self._skills)

	def set_skip(self, skip: bool):
		self.skip = skip

	def set_threads(self, threads: int):
		self.workers = threads

	def stop(self):
		self._skills.clear()
		while len(self.threads) > 0:
			pass

	def run(self):
		self.stop()

		self._skills.clear()
		self._downloads = 0
		self._passed = 0
		self.threads = dict()

		for skillid in range(self.max):
			if self.skip and os.path.exists(f'{self.path}/{skillid}.jpg'):
				continue

			self._skills.append(skillid)

		self._queued = len(self._skills)

		for thread_id in range(self.workers):
			self.threads[thread_id] = threading.Thread(target=self._threadrunner, args=(thread_id,), daemon=True)
			self.threads_downloads[thread_id] = 0

		for thread_id in range(self.workers):
			self.threads[thread_id].start()

	def _threadrunner(self, thread_id):
		while len(self._skills) > 0:
			if self.threads[thread_id] is None:
				return

			with self._skilllock:
				next_skill = self._skills.pop(0)

			if self._download_skill(next_skill):
				self.threads_downloads[thread_id] += 1
		del self.threads[thread_id]

	def _download_skill(self, skillid):
		with self._passlock:
			self._passed += 1

		request = requests.get(_URL.format(skillid), stream=True)
		if request.status_code != 200:
			return False

		data = request.raw
		data.decode_content = True

		with open(f'{self.path}/{skillid}.jpg', 'wb') as f:
			shutil.copyfileobj(data, f)

		with self._lock:
			self._downloads += 1

		return True

	def get_percentage(self):
		try:
			return self._passed / self._queued
		except ZeroDivisionError:
			return 0

	def get_downloads(self):
		return self._downloads

	def is_running(self):
		for key in self.threads:
			try:
				if self.threads[key].is_alive():
					return True
			except KeyboardInterrupt:
				return False

		return False
