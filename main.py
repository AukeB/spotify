'''
Automatically creates a Spotify playlist from all the songs that have been shared in a single whatsapp conversation.
Written by: Auke Bruinsma

Steps.
1. Import whatsapp conversation from .txt file.
2. Format the Whatsapp conversation into a Pandas DataFrame.
3. Obtain a DataFrame which contains only messages that contain Spotify links in them.
4. Create a list with just the Spotify URIs.
5. Create a Spotify playlist with these tracks.

TODO:
- BUG: Hij pakt niet alle tracks.
- Display
	- Number of messages
	- Number of messages containing spotify links
		- Tracks
		- Albums
		- Playlists
- Convert URLs to urls. DONE
- Check if playlist already exists. DONE
	- If so, check if there are any tracks not in this playlist and update the playlist DONE.
	- If not create the playlist and add tracks DONE.
- Make an UI.
'''

 ### Imports ###

import pandas as pd
import logging
import requests
import parameters as p

 ### Settings ###

logging.basicConfig(level=p.LOGGING_LEVEL) # Set the logging level.

 ### Functions ###

def import_whatsapp_conversation(file_path: str) -> list:
	'''
	Imports Whatsapp conversation and returns it in raw form.

	Args:
		file_path (str):		Path to the file that contains the whatsapp conversation.

	Returns:
		lines (list):			List that contains the conversation.
	'''

	# Open the file.
	with open(file_path, encoding="utf8") as f:
		lines = f.readlines()

	return lines

def format_whatsapp_conversation(raw_text) -> pd.DataFrame():
	'''
	Executes the following tasks:
	1. 
	
	'''
	def replace_enters(raw_text: str) -> str:
		'''
		Delete all enters from the text file and replace them with a space.

		Args:
			raw_text (string):			Raw text file.

		Returns:
			text (string):				Text file but now without enters.
		'''

		text = [x.replace('\n',' ') for x in raw_text]
		return text

	def format_messages(text: str) -> str:
		'''
		Sometimes the message part of a line in the text file is spread out over several lines. This
		means that a list element does not always begin with a date, but with the second part of the previous message.
		This causes a problem and this function solves that.

		Args:
			text (str):					Text file.

		Returns
			text (str):					Text file but now with each list element starting with the date.
		'''

		length = len(text) - 2 # Length is set a bit shorter than true length because we are comparing to future elements.
		i = 0 # Counter.

		# Loop through the whole Whatsapp conversation.
		while i <= length:
			c = False
			while c == False:
				next_date_element = text[i+1].split(',')[0] # Obtain the element which should be a date.
				# Criteria for a date (Hopefully there are no elemnents which fit these criteria that are not a date.
				if len(next_date_element) <= 8 and next_date_element.count('/') == 2:
					i += 1 # Increase counter if everything goes correctly.
					c = True
					break # Stop loop element.
				else:
					text[i:i+2] = [''.join(text[i:i+2])] # Merge two elements.
					length -= 1 # Decrease length because of executed merge.

		return text

	def convert_to_dataframe(text: str) -> pd.DataFrame():
		'''
		This functions takes the list as input. Each element of the list is divided into
		a date part, time part, sender part and a message part. This different parts are all 
		added to a list, and finally converted to a Pandas DataFrame.

		Args:
			text (str):					Text file containing the Whatsapp conversation.

		Returns:
			df (pd.DataFrame()):		Whatsapp conversation but now in DataFrame format.
		'''

		# Create empty lists in which the different types of elements will be stored.
		date_list = []
		time_list = []
		sender_list = []
		message_list = []

		# Loop through all list elements.
		for i in range(len(text)):
			# Divide all lines into different parts.
			s1 = text[i].split(', ') # Divide the text so that s1[0] is the date part and s[1] contains the time, sender and message.
			if len(s1) > 2: s1[1:] = [''.join(s1[1:])] # If a comma occurs multiple times, merge the elements.

			s2 = s1[1].split(' - ') # Divide s1 so that s2[0] is the time part and s2[1] is the sender + the message
			if len(s2) > 2: s2[1:] = [''.join(s2[1:])] # Same but now with the ' - ' part.

			s3 = s2[1].split(': ') # Divide s2 so that s3[0] is the sender and s3[1] is the message.
			# If there is no sender of the message, add the sender column and leave it empty.
			# Occurs at least once, at the beginning of the conversation.
			if len(s3) == 1:
				s3 = ['', s3[0]]
			if len(s3) > 2: s3[1:] = [''.join(s3[1:])] # Same but now with the ':' part.

			# Append all individual elements to the lists.
			date_list.append(s1[0])
			time_list.append(s2[0])
			sender_list.append(s3[0])
			message_list.append(s3[1])
		
		# Convert lists to DataFrames.
		df = pd.DataFrame(list(zip(date_list, time_list, sender_list, message_list)),
				columns=['Date', 'Time', 'Sender', 'Message'])

		logging.info(f' Whatsapp conversation contains {df.shape[0]} messages.')

		return df


	# Delete all enters from chat.
	text = replace_enters(raw_text)

	# Make sure all the message elements in the array are located in a single array element.
	text = format_messages(text)

	# Convert to DataFrame.
	df = convert_to_dataframe(text)

	return df

def select_rows(df) -> pd.DataFrame():
	'''
	Obtains all rows from the dataframe which have Spotify links in the 'Message' column.

	Args:
		df (pd.DataFrame()):					Whatsapp conversation DataFrame.

	Returns
		spotify_df (pd.DataFrame()):			DataFrame but now with only Spotify links.
	'''

	# Create empty dataframe.
	spotify_df = pd.DataFrame()

	if p.TRACKS: # Add messages that contain links to tracks.
		df_temp = df[df['Message'].str.contains(p.TRACK_URL)]
		spotify_df = spotify_df.append(df_temp, ignore_index=True)
		logging.info(f'  Number of tracks: {df_temp.shape[0]}')

	if p.ALBUMS: # Add messages that contain links to albums.
		df_temp = df[df['Message'].str.contains(p.ALBUM_URL)]
		spotify_df = spotify_df.append(df_temp, ignore_index=True)
		logging.info(f'  Number of albums: {df_temp.shape[0]}')

	logging.info(f' In total, {spotify_df.shape[0]} messages contain Spotify links.')

	return spotify_df

def obtain_all_urls(df) -> list:
	'''
	Obtains just the Spotify urls from the DataFrame and appends them all to a list.

	Args:
		df (pd.DataFrame()):					Whatsapp conversation DataFrame.

	Returns:
		spotify_list (list):					The list containing all the urls.
	'''

	column = df['Message']
	spotify_list = []

	for _, value in column.items():
		elements = value.split(' ')
		for j in elements:
			if 'https://' in j:
				spotify_list.append(j)

	return spotify_list

def convert_albums_to_tracks(uri_list: list) -> list:
	'''
	This function only gets called if the user wants to add whole albums to
	the playlist. Albums will be detected in the list of URIs, all the tracks from those
	albums will be added to the list, and the ablum URI itself will be removed:

	Args:
		uri_list (list):			The list of URIs, with the albums in it.

	Returns
		uri_list (list):			The list of URIs, but now containing the tracks from
									the album(s), instead of the album itself.
	'''

	track_uri_list = [x for x in uri_list if 'track' in x]
	album_uri_list = [x for x in uri_list if 'album' in x]
	track_counter = 0

	for album_uri in album_uri_list:
		response = requests.get(
				f'https://api.spotify.com/v1/albums/{album_uri.split(":")[-1]}',
				headers = {
					'Authorization': f'Bearer {p.ACCESS_TOKEN}'
				},
			)
			
		album_dict = response.json()

		for item in album_dict['tracks'].get('items', {}):
			track_uri_list.append(f'spotify:track:{item.get("id")}')
			track_counter += 1

	logging.info('')
	logging.info(f' The {len(album_uri_list)} album(s) contain a total of {track_counter} tracks, which will be added to the playlist.')

	return track_uri_list


def convert_url_to_uri(url_list: list) -> list:
	'''
	Converts the Spotify URLs to URIs, because the API needs this as input for a track.

	Args:
		url_list (list):				A list containing all the Spotify URLs for each track.

	Returns:
		uri_list (list):				The same list but now with URIs instead of URLs.
	'''

	uri_prefix = 'spotify:track:' # The prefix with which each URI starts.
	uri_list = [] # List in which all the URIs will be stored.

	# Loop through all tracks.
	for url in url_list:
		sub_string_1 = url.split('https://open.spotify.com/')[1] # Remove the first part of the URL because it is not relevant for the URI.
		sub_string_2 = sub_string_1.split('/') # substring_2 will contain the identifer for a track, album, playlist, etc.
		sub_string_3 = sub_string_2[1].split('?')[0] # Obtain the part before the question mark.
		uri = f'spotify:{sub_string_2[0]}:{sub_string_3}' # Establish the URI.
		uri_list.append(uri) # Append it to the list.

	if p.ALBUMS:
		uri_list = convert_albums_to_tracks(uri_list)

	return uri_list


def create_playlist(
		tracks,
		name=p.PLAYLIST_NAME,
		description=p.PLAYLIST_DESCRIPTION,
		public=p.PUBLIC
	) -> None:

	'''


	Args:


	Returns:

	'''

	def obtain_playlist_id(name: str) -> str:
		'''


		Args:


		Returns:

		'''

		response = requests.get(
			p.SPOTIFY_CREATE_PLAYLIST_URL,
			headers = {
				'Authorization': f'Bearer {p.ACCESS_TOKEN}'
			},
		)
		
		playlist_dict = response.json()

		for item in playlist_dict.get('items', {}):
			if item.get('name') == name:
				return item.get('id')

	def get_playlist_items(playlist_id: str) -> list:
		'''


		Args:


		Returns:

		'''

		response = requests.get(
			url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
			headers = {
				'Authorization': f'Bearer {p.ACCESS_TOKEN}'
			},
		)

		# Get playlist information in dictionary.
		playlist_items = response.json()

		# Obtain the URIs for all the tracks in the playlist.
		track_uris = [x.get('track').get('uri') for x in playlist_items.get('items', {})]
		
		return track_uris

	def obtain_new_tracks(tracks: str, already_added_tracks: str) -> list:
		'''


		Args:


		Returns:

		'''

		# Obtain the new tracks.
		new_tracks = list(set(tracks) - set(already_added_tracks))
		return new_tracks

	def get_users_playlists() -> list:
		'''


		Args:


		Returns:

		'''

		response = requests.get(
			url=p.SPOTIFY_CREATE_PLAYLIST_URL,
			headers = {
				'Authorization': f'Bearer {p.ACCESS_TOKEN}'
			},
		)
		
		# Obtain playlist dictionary.
		playlist_dict = response.json()

		# Obtain a list of the user's playlist names.
		playlist_names = [x.get('name') for x in playlist_dict.get('items', {})] 

		return playlist_names

	def create_playlist_on_spotify(name=name, description=description, public=public):
		'''


		Args:


		Returns:

		'''

		response = requests.post(
			url=p.SPOTIFY_CREATE_PLAYLIST_URL,
			headers = {
				'Authorization': f'Bearer {p.ACCESS_TOKEN}'
			},
			json = {
				'name': name,
				'description': description,
				'public': public
			}
		)

		json_resp = response.json()

		return json_resp

	def add_items_to_playlist(tracks: list, playlist_id: str):
		'''


		Args:


		Returns:

		'''

		def make_request(tracks: list, playlist_id: str):
			'''


			Args:


			Returns:

			'''

			response = requests.post(
				url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
				headers = {
					'Authorization': f'Bearer {p.ACCESS_TOKEN}'
				},
				json = {
					'uris': tracks
				}
			)

			snapshot_id = response.json()

			return snapshot_id

		if len(tracks) <= 100:
			snapshot_id = make_request(tracks, playlist_id)
		else:
			counter = 0
			while counter*100 <= len(tracks):
				snapshot_id = make_request(tracks[counter*100:(counter+1)*100], playlist_id)
				counter += 1

		return snapshot_id


	# Obtain Spotify users's playlists.
	playlist_name_list = get_users_playlists()

	if p.PLAYLIST_NAME in playlist_name_list:
		logging.info(' Playlist already exists. New tracks will be added to this playlist.')

		# Obtain the playlist id.
		playlist_id = obtain_playlist_id(name=p.PLAYLIST_NAME)

		# Obtain a list of all the playlist items.
		current_tracks_in_playlist = get_playlist_items(playlist_id=playlist_id)

		# Obtain the tracks which are not yet in the playlist.
		tracks = obtain_new_tracks(tracks=tracks, already_added_tracks=current_tracks_in_playlist)

		# Add tracks to playlist.
		if tracks:
			logging.info(f' {len(tracks)} new track(s) found and is/are added to the playlist.')
			snapshot_id = add_items_to_playlist(tracks=tracks, playlist_id=playlist_id)
		else:
			logging.info(' No new tracks are present in the current Whatsapp conversation. Playlist not updated.')

	else:
		# Create playlist.
		logging.info(' Playlist does not exist yet and will now be created.')
		playlist = create_playlist_on_spotify(name=p.PLAYLIST_NAME, description=p.PLAYLIST_DESCRIPTION, public=p.PUBLIC)

		# Obtain the newly created playlist id.
		playlist_id = obtain_playlist_id(name=p.PLAYLIST_NAME)

		print(tracks)

		# Add tracks to playlist.
		snapshot_id = add_items_to_playlist(tracks=tracks, playlist_id=playlist_id)
	

def main():
	# Import Whatsapp conversation.
	raw_text = import_whatsapp_conversation(p.TEXTFILE_PATH)

	# Convert it to a Pandas Dataframe.
	text_df = format_whatsapp_conversation(raw_text)

	# Obtain all rows which have Spotify links in them.
	spotify_df = select_rows(text_df)

	# Obtain a list of the URL links to the tracks.
	spotify_url_list = obtain_all_urls(spotify_df)

	# Convert URLs to URIs
	spotify_uri_list = convert_url_to_uri(spotify_url_list)

	# Create the playlist
	create_playlist(tracks=spotify_uri_list)


if __name__ == '__main__':
	main()
