# This script is first generated by Bing AI, and then modified by the author.


# Import the libraries
import time
import requests
from bs4 import BeautifulSoup, element
import os
import json
import sys
from collections import OrderedDict

# Create a session object
session = requests.Session()

# Use the existing data to log in
# You need to fill in the details of your existing data
# session.cookies.update({"cookie_name": "cookie_value"})
session.cookies.update({"cookie": ""})
session.headers.update({"user-agent": ""})
tid = sys.argv[1]
path = "./" if len(sys.argv) == 2 else sys.argv[2]
if not os.path.exists(path):
    os.mkdir(path)

# Find Title
url = f"https://nga.178.com/read.php?tid={tid}"
response = session.get(url)
soup = BeautifulSoup(response.content, "html.parser")
subject = soup.find("h3").text
dirname = subject + '_' + tid
print(subject)
dirname = os.path.join(path, dirname)

# Create an empty list to store the data
data = OrderedDict()
lastindex = -1
flgStop = False
if not os.path.exists(dirname):
    os.mkdir(dirname)

# Loop through the pages of the thread
for page in range(1, 700):
    # Get the URL of the page
    url = f"https://nga.178.com/read.php?tid={tid}&page={page}"
    # Get the response from the URL
    response = session.get(url)
    # Create a BeautifulSoup object from the response
    soup = BeautifulSoup(response.content, "html.parser")
    # Find all the div tags with the class name postcontent ubbcode
    tables = soup.find_all("table", class_="forumbox postbox")
    # Loop through the div tags
    for table in tables:
        # find the speaker, time
        posterInfo = table.find("a", class_="author b").attrs["href"].split("uid=")[1]
        postInfo = table.find(class_="postInfo").text

        # find the content
        content = table.find(class_='postcontent ubbcode')
        index = content.attrs["id"][11:]
        print(posterInfo, postInfo, index)
        if int(index) <= lastindex:
            flgStop = True
            break
        # extract contents
        saved_contents = []
        for ct in content.contents:
            if isinstance(ct, element.Tag):
                # <br/>
                ct = ""
            elif isinstance(ct, element.NavigableString):
                ct = ct.text
            else:
                import pdb; pdb.set_trace()
            saved_contents.append(ct)

            # download images
            img_urls = ct.split("[img]")[1:]
            for img in img_urls:
                img = img.split("[/img]")
                if len(img) == 2:
                    src = img[0] if img[0].startswith("http") else "https://img.nga.178.com/attachments/" + img[0]
                    # download img
                    print(f"downloading {src} ...")
                    r = requests.get(src)
                    with open(f"{dirname}/{src.split('/')[-1]}", "wb") as f:
                        f.write(r.content)
                    if img[0].endswith(".medium.jpg"):
                        src = src.replace(".medium.jpg", "")
                        print(f"downloading {src} ...")
                        r = requests.get(src)
                        with open(f"{dirname}/{src.split('/')[-1]}", "wb") as f:
                            f.write(r.content)
            # Append the src to the data list
            # data.append(src)
        # Append the text to the data list
        data[index] = {
            "author": posterInfo,
            "time": postInfo,
            "content": saved_contents,
        }
        lastindex = int(index)
    if flgStop:
        break
    time.sleep(3)

# compare and update
if os.path.exists(f"{dirname}/last_json"):
    with open(f"{dirname}/last_json", "r", encoding="utf-8") as f:
        last_filename = f.readline().strip()
    with open(last_filename, "r", encoding="utf-8") as f:
        last_json = json.load(f)
    old_keys = last_json.keys()
    new_keys = data.keys()
    all_keys = list(set([int(k) for k in old_keys] + [int(k) for k in new_keys]))
    all_keys.sort()
    new_data = OrderedDict()
    for key in all_keys:
        key = str(key)
        if key in last_json:
            if key not in data:
                new_data[key] = last_json[key]
            else:
                # compare
                same = len(last_json[key]["content"]) == len(data[key]["content"])
                cmpall = [oi == ni for oi, ni in zip(last_json[key]["content"], data[key]["content"])]
                same = same and all(cmpall)
                if same:
                    new_data[key] = data[key]
                else:
                    print(">> old >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    for item in last_json[key]["content"]:
                        print(item)
                    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< new <<")
                    for item in data[key]["content"]:
                        print(item)
                    print("*************** [O]ld or [N]ew ****************")
                    while True:
                        s = input()
                        if s[0] in ["O", "o"]:
                            new_data[key] = last_json[key]
                            print("Choosing Old")
                            break
                        elif s[0] in ["N", "n"]:
                            new_data[key] = data[key]
                            print("Choosing New")
                            break
                        elif s[0] in ["C", "c"]:
                            new_data[key] = last_json[key]
                            new_data[key]["content"].append("************** UPDATE **************")
                            new_data[key]["content"].extend(data[key]["content"])
                            print("Combining Both")
                            break
        else:
            new_data[key] = data[key]
    data = new_data
    

# save a json file
new_filename = f"{dirname}/{time.strftime('%Y%m%d-%H%M%S')}.json"
with open(new_filename, 'w', encoding='utf-8') as f:
    json.dump(data, fp=f, indent=4, ensure_ascii=False)
# note the last json file
with open(f"{dirname}/last_json", "w", encoding="utf-8") as f:
    f.write(new_filename)

with open(f"{dirname}/README.md", 'w', encoding='utf-8') as f:
    f.write(f"## {subject}\n\n")
    for key, value in data.items():
        f.write(f"### {key} {value['author']} {value['time']}\n")
        for item in value["content"]:
            # replace image
            subitems = item.split("[img]")
            for i in range(len(subitems)):
                if "[/img]" in subitems[i]:
                    img_url, others = subitems[i].split("[/img]")
                    subitems[i] = f"![img]({img_url.split('/')[-1]} 'img')" + others
            item = "".join(subitems)

            f.write(f"{item}\n")
