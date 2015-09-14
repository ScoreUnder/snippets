#!/usr/bin/env python3
# Python reimplementation of the 8chan-download shell script
# found at https://github.com/ScoreUnder/scripts-and-dotfiles/blob/master/bin/8chan-download
from collections import namedtuple
import json
import sys
import itertools
from urllib.request import urlopen, Request
from urllib.error import HTTPError

if len(sys.argv) != 2:
    print("Please supply a thread URL to download", file=sys.stderr)
    exit(1)

thread = sys.argv[1].split('#')[0]
if thread.endswith("html"):
    thread = thread[:-len("html")] + "json"

board = thread.split('/res/')[0].split('/')[-1]
base_url = "https://8ch.net/{board}/src/".format(board=board)

# The cripple has banned python bots from the site so we have to fake it
my_headers = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)'}

with urlopen(Request(thread, headers=my_headers)) as response:
    json_response = json.loads(response.read().decode('utf-8', 'replace'))

ImageFile = namedtuple('ImageFile', ('source_url', 'dest_filename'))

images = []
for post in json_response['posts']:
    # Search the post and its "extra_files" (and they have the same format)
    for image in itertools.chain([post], post.get('extra_files', [])):
        time = image.get('tim')
        if time is None:  # A post has a "tim" iff it has an attachment
            continue

        filename = image.get('filename', '')
        extension = image.get('ext', '')

        source_url = "%s%s%s" % (base_url, time, extension)

        # Coerce filename & extension to string, split on slash to prevent
        # directory traversal
        partial_filename = ("%s%s" % (filename, extension)).split('/')[-1]
        time = str(time).split('/')[-1]
        # Always prefix image upload time to ensure a unique filename
        dest_filename = "%s_%s" % (time, partial_filename)

        images.append(ImageFile(source_url, dest_filename))


for image in images:
    # Note: the bash script will continue failed downloads and skip already
    # downloaded images, as well as showing progress.
    # This script will do none of those things.
    # This will also buffer the entire file in memory before writing it,
    # meaning you can't partially download images and the script will take
    # up as much memory as the file is large.
    try:
        with open(image.dest_filename, 'wb') as dest:
            with urlopen(Request(image.source_url, headers=my_headers)) as source:
                dest.write(source.read())
    except (HTTPError, URLError, IOError) as e:
        print("Failed to download '{source}' to '{dest}'.".format(source=image.source_url, dest=image.dest_filename), file=sys.stderr)
        print(str(e), file=sys.stderr)
