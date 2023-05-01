# Anki2Toggl v1.0.0

from collections import namedtuple
from datetime import datetime, timezone
import os
import requests
import sqlite3
import sys

####################################################################################################
# Config section below :
####################################################################################################
# Anki configuration
ANKI_PROFILE = 'User 1'
ALL_REVIEWS_FROM_DTIME = '2023-01-01T00:00:00Z'
BATCHING_ANKI_REVIEWS_THRESHOLD_IN_SEC = 120 # 120 secs = 2 min

# Toggl configuration
API_TOKEN = 'y0urAP1T0k3n'
WORKSPACE_NAME = 'Your Name\'s workspace'
PROJECT_NAME = 'Priming' # Default: 'Priming' (as per Refold's recommendation)
TIME_ENTRY_DESCRIPTION = 'Anki Review' # Default: 'Priming' (as per Refold's recommendation)
####################################################################################################
# Config section above ^
####################################################################################################

####################################################################################################
USERNAME = API_TOKEN
PASSWORD = 'api_token' # When using the API Token, Toggl uses 'api_token' as password for the authentication

ALL_REVIEWS_FROM_DTIME_IN_EPOCH = int(datetime.fromisoformat(ALL_REVIEWS_FROM_DTIME).timestamp())
TIME_ENTRY_CREATED_WITH = 'Anki2Toggl'
####################################################################################################

def get_anki_profiles():
	anki_profiles = []
	for filename in os.listdir(anki_path):
		if not os.path.isdir(os.path.join(os.path.abspath(anki_path), filename)):
			continue
		if filename=='addons21':
			continue
		anki_profiles.append(filename)

	return anki_profiles

def get_anki_collection_db_path(anki_profile):
	return os.path.join(os.getenv('APPDATA'), 'Anki2', anki_profile, 'collection.anki2')

# From : https://docs.ankiweb.net/stats.html#manual-analysis
# 0 id              epoch-milliseconds timestamp of when you did the review
# 1 cid             cards.id
# 2 usn             update sequence number: for finding diffs when syncing. 
# 3 ease            which button you pushed to score your recall.  review:  1(wrong), 2(hard), 3(ok), 4(easy) - learn/relearn:   1(wrong), 2(ok), 3(easy)
# 4 ivl             interval (i.e. as in the card table)
# 5 lastIvl         last interval (i.e. the last value of ivl. Note that this value is not necessarily equal to the actual interval between this review and the preceding review)
# 5 factor          factor
# 7 time            how many milliseconds your review took, up to 60000 (60s)
# 8 type            0=learn, 1=review, 2=relearn, 3=cram
AnkiReview = namedtuple('AnkiReview', 'id, cid, usn, ease, ivl, lastIvl, factor, time, type')
def get_anki_reviews(db_path, reviews_from_in_epoch):
	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	c.execute('SELECT * from revlog WHERE id > {}'.format(reviews_from_in_epoch))

	reviews = []
	for r in map(AnkiReview._make, c.fetchall()):
		reviews.append(r)
	
	conn.close()

	return reviews

def get_toggl_auth(username, password):
	url = 'https://api.track.toggl.com/api/v9/me'
	r = requests.get(url, auth=(username, password), headers={'content-type': 'application/json'}) 
	r.raise_for_status()

	return r.json()

def get_toggl_workspaces(username, password):
	url = 'https://api.track.toggl.com/api/v9/workspaces'
	r = requests.get(url, auth=(username, password), headers={'content-type': 'application/json'}) 
	r.raise_for_status()

	return r.json()

def get_toggl_workspace_by_name(username, password, workspace_name):
	workspaces = get_toggl_workspaces(API_TOKEN, PASSWORD)

	workspace = None
	for w in workspaces:
		if w['name']==workspace_name:
			workspace = w
			break

	return workspace

def get_toggl_projects(username, password, workspace_id):
	url = 'https://api.track.toggl.com/api/v9/workspaces/{}/projects'.format(workspace_id)
	r = requests.get(url, auth=(username, password), headers={'content-type': 'application/json'}) 
	r.raise_for_status()

	return r.json()

def get_toggl_projects_by_name(username, password, workspace_id, project_name):
	projects = get_toggl_projects(API_TOKEN, PASSWORD, workspace_id)

	project = None
	for p in projects:
		if p['name']==project_name:
			project = p
			break

	return project

def get_toggl_time_entries(username, password):
	url = 'https://api.track.toggl.com/api/v9/me/time_entries'
	r = requests.get(url, auth=(username, password), headers={'content-type': 'application/json'}) 
	r.raise_for_status()

	return r.json()

def get_toggl_time_entries_by_description(username, password, time_description):
	time_entries = get_toggl_time_entries(API_TOKEN, PASSWORD)

	time_entries_filtered = []
	for te in time_entries:
		if te['description']==time_description:
			time_entries_filtered.append(te)

	return time_entries_filtered

def post_toggl_time_entries(username, password, workspace_id, time_entries):
	for time_entry in time_entries:
		post_toggl_time_entry(username, password, workspace_id, time_entry)

def post_toggl_time_entry(username, password, workspace_id, time_entry):
	url = 'https://api.track.toggl.com/api/v9/workspaces/{}/time_entries'.format(workspace_id)
	print(time_entry['start'])
	r = requests.post(url, json=time_entry, auth=(username, password), headers={'content-type': 'application/json'})
	print(r.json())
	r.raise_for_status()
	sys.stdout.flush()

def delete_toggl_time_entries(username, password, workspace_id, time_entries):
	for time_entry in time_entries:
		delete_toggl_time_entry(username, password, workspace_id, time_entry)

def delete_toggl_time_entry(username, password, workspace_id, time_entry):
	url = 'https://api.track.toggl.com/api/v9/workspaces/{}/time_entries/{}'.format(workspace_id, time_entry['id'])
	print(time_entry['id'])
	r = requests.delete(url, auth=(username, password), headers={'content-type': 'application/json'}) 
	r.raise_for_status()
	sys.stdout.flush()

def batch_anki_reviews(anki_reviews, batching_threshold_in_sec):
	if not anki_reviews or batching_threshold_in_sec==0:
		return anki_reviews

	def by_start_dtime(r): return r.id
	anki_reviews.sort(key=by_start_dtime)

	batching_threshold_in_ms = batching_threshold_in_sec * 1000
	
	batched_anki_reviews = [anki_reviews[0]]
	last_r = batched_anki_reviews[-1]

	for r in anki_reviews[1:]:
		last_start = last_r.id
		last_duration = last_r.time
		last_stop = last_start + last_duration
		curr_start = r.id
		curr_duration = r.time

		diff = curr_start - last_stop

		new_r = None
		if diff < batching_threshold_in_ms:
			new_r = batched_anki_reviews.pop()._replace(time=last_duration + diff + curr_duration)
		else:
			new_r = r
		
		batched_anki_reviews.append(new_r)
		last_r = new_r

	return batched_anki_reviews

def main():
	# workspace = get_toggl_workspace_by_name(USERNAME, PASSWORD, WORKSPACE_NAME)
	# if workspace is None:
	# 	print('No \'{}\' workspace found.'.format(WORKSPACE_NAME))
	# 	return
	# time_entries = get_toggl_time_entries_by_description(USERNAME, PASSWORD, TIME_ENTRY_DESCRIPTION)
	# delete_toggl_time_entries(USERNAME, PASSWORD, workspace['id'], time_entries)
	# return

	time_entries = get_toggl_time_entries_by_description(USERNAME, PASSWORD, TIME_ENTRY_DESCRIPTION)

	last_stop_dtime_epoch = None
	for te in time_entries:
		current_stop_dtime_epoch = int(datetime.fromisoformat(te['stop']).timestamp())
		if last_stop_dtime_epoch is None or last_stop_dtime_epoch < current_stop_dtime_epoch:
			last_stop_dtime_epoch = current_stop_dtime_epoch

	from_epoch = ALL_REVIEWS_FROM_DTIME_IN_EPOCH if last_stop_dtime_epoch is None else max(ALL_REVIEWS_FROM_DTIME_IN_EPOCH, last_stop_dtime_epoch + 1)
	
	# From Anki
	anki_reviews = get_anki_reviews(get_anki_collection_db_path(ANKI_PROFILE), from_epoch * 1000)
	if not anki_reviews:
		print('No new Anki reviews to synchronize. Toggl is already up-to-date.')
		return

	# Into Toggl
	workspace = get_toggl_workspace_by_name(USERNAME, PASSWORD, WORKSPACE_NAME)
	if workspace is None:
		print('No \'{}\' workspace found.'.format(WORKSPACE_NAME))
		return
	
	project = get_toggl_projects_by_name(USERNAME, PASSWORD, workspace['id'], PROJECT_NAME)
	if project is None:
		print('No \'{}\' project found.'.format(PROJECT_NAME))
		return

	batched_anki_reviews = batch_anki_reviews(anki_reviews, BATCHING_ANKI_REVIEWS_THRESHOLD_IN_SEC)

	time_entries = []
	for r in batched_anki_reviews:
		time_entry = {
			'created_with': TIME_ENTRY_CREATED_WITH,
			'description': TIME_ENTRY_DESCRIPTION,
			'project_id': project['id'],
			'workspace_id': workspace['id'],
			'start': datetime.fromtimestamp(int(int(r.id) / 1000), timezone.utc).isoformat(),
			'duration': int(int(r.time) / 1000)
		}
		time_entries.append(time_entry)

	post_toggl_time_entries(USERNAME, PASSWORD, workspace['id'], time_entries)
	
if __name__ == '__main__':
    main()